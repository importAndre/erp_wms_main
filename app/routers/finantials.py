from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends, UploadFile, File, Query, HTTPException, status
from ..schemas import finantialsSchemas, productSchemas, compositionSchemas
from ..models import finantialsModels, suppliersModels, identificatorsModels, accountModels
from ..oauth2 import get_current_user
from ..server_config import API_URL
import requests, json
from typing import Optional, Union, List
from ..services import userServices, mercadoLivreServices, finantialServices, productServices, compositionServices
from sqlalchemy.orm import Session
from ..database import get_db
from ..services import userServices, companyServices
from calendar import monthrange
from .suppliers import get_payments
from .mercado_livre import get_infos
import pandas as pd
from io import BytesIO
from sqlalchemy import or_

router = APIRouter(
    prefix="/finantials",
    tags=["Finantials"]
)


@router.post("/upload-xml")
def upload_invoice_xml(
    xml_file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    url = f"{API_URL}/invoices/upload"  # endpoint da primeira função

    req = requests.post(
        url,
        files={
            "xml_file": (
                xml_file.filename,
                xml_file.file,  # envia o stream direto
                xml_file.content_type or "application/xml",
            )
        },
        timeout=60,
    )

    return req.json()

@router.get("/invoices")
def get_invoices(
    cnpj: Optional[str] = None, 
    date_begin: Optional[str] = None,
    date_end: Optional[str] = None,
    emit: bool = False
    ):
    url = f"{API_URL}/invoices"
    params = {
        "cnpj": cnpj,
        "emit": emit,
        "date_begin": date_begin,
        "date_end": date_end
    }
    req = requests.get(url=url, timeout=30, params=params)
    if req.status_code == 200:
        data = req.json()
        return data


@router.post("/taxes", response_model=finantialsSchemas.SellTaxesResponse)
def register_payment(
    taxes: finantialsSchemas.SellTaxesCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_payment = finantialsModels.Taxes(
        company_id=taxes.company_id,
        taxes_name=taxes.taxes_name,
        detail=taxes.detail,
        value=taxes.value,
        reference=taxes.reference,
        payment_date=taxes.payment_date        
    )
    db.add(new_payment)
    db.commit()
    db.refresh(new_payment)
    return new_payment

@router.post("/fixos", response_model=finantialsSchemas.FixosResponse)
def register_payment(
    payment: finantialsSchemas.FixosCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_payment = finantialsModels.Fixos(
        company_id=payment.company_id,
        name=payment.name,
        detail=payment.detail,
        value=payment.value,
        payment_date=payment.payment_date        
    )
    db.add(new_payment)
    db.commit()
    db.refresh(new_payment)
    return new_payment

balance_cache = {}
dre_cache = {}


def _report_cache_key(
    company_id: int,
    date_begin: date,
    date_end: date,
    show_details: bool
):
    return (
        company_id,
        date_begin.isoformat(),
        date_end.isoformat(),
        bool(show_details)
    )


def _save_report_cache(cache: dict, key: tuple, value, max_items: int = 100):
    if key not in cache and len(cache) >= max_items:
        oldest_key = next(iter(cache))
        cache.pop(oldest_key)
    cache[key] = value


@router.get("/balance", response_model=finantialsSchemas.BalancoPatrimonial)
def get_balance(
    company_id: int,
    date_begin: date,
    date_end: date,
    show_details: Optional[bool] = False,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
) -> finantialsSchemas.BalancoPatrimonial:
    cache_key = _report_cache_key(
        company_id=company_id,
        date_begin=date_begin,
        date_end=date_end,
        show_details=show_details
    )
    if cache_key in balance_cache:
        return balance_cache[cache_key]

    balance = finantialServices.PatrimonialBalance(
        company_id=company_id,
        date_begin=date_begin,
        date_end=date_end,
        db=db
    ).get_balance(show_details=show_details)

    _save_report_cache(balance_cache, cache_key, balance)
    return balance


@router.get("/dre", response_model=finantialsSchemas.DRE)
def get_dre(
    company_id: int,
    date_begin: date,
    date_end: date,
    show_details: Optional[bool] = False,
    desired_margin: Optional[float] = 10,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
) -> finantialsSchemas.DRE:
    cache_key = _report_cache_key(
        company_id=company_id,
        date_begin=date_begin,
        date_end=date_end,
        show_details=show_details
    )
    if cache_key in dre_cache:
        return dre_cache[cache_key]

    dre = finantialServices.Dre(
        company_id=company_id,
        date_begin=date_begin,
        date_end=date_end,
        db=db
    ).get_dre(show_details=show_details, desired_margin=desired_margin)

    _save_report_cache(dre_cache, cache_key, dre)
    return dre


@router.get("/cash-flow", response_model=finantialsSchemas.DFC)
def get_cash_flow(
    company_id: int,
    date_begin: date,
    date_end: date,
    future_date: Optional[date] = None,
    show_details: Optional[bool] = False,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
) -> finantialsSchemas.DFC:
    return finantialServices.CashFlow(
        company_id=company_id,
        date_begin=date_begin,
        date_end=date_end,
        future_date=future_date,
        db=db
    ).get_cashflow(show_details=show_details)



def get_product_by_cprod(c_prod, sup_cnpj, db: Session = Depends(get_db)):
    query = db.query(identificatorsModels.Identificators).filter(identificatorsModels.Identificators.value == c_prod)\
        .filter(identificatorsModels.Identificators.identif_type == 'supplier_code').all()
    
    for p in query:
        if p.is_composition:
            comp = compositionServices.Composition(cid=p.composition_id, db=db).get_composition()
            for i in comp.items:
                if i.product.supplier.cnpj == sup_cnpj:
                    return comp
        if not p.is_composition:
            prod = productServices.Product(pid=p.product_id, db=db).get_product()
            if prod.supplier.cnpj == sup_cnpj:
                return prod
    return None


def get_invoices_products(data, db: Session = Depends(get_db), vendas: bool = False):
    result = []
    from .products import search_by_sku

    if vendas:
        for nf in data['invoices']:
            nf_schema = finantialsSchemas.InvoiceBase.model_validate(nf)
            for i in nf_schema.items:
                prod = search_by_sku(sku=i.c_prod, db=db)
                if isinstance(prod, productSchemas.ProductResponse):
                    result.append(
                        {
                            "product": prod,
                            "amount": i.q_com
                        }
                    )
                elif isinstance(prod, compositionSchemas.CompositionResponse):
                    for item in prod.items:
                        result.append(
                            {
                                "product": item.product,
                                "amount": i.q_com * item.amount_required
                            }
                        )




    for nf in data['invoices']:
        nf_schema = finantialsSchemas.InvoiceBase.model_validate(nf)
        for i in nf_schema.items:
            prod = get_product_by_cprod(c_prod=i.c_prod, sup_cnpj=nf_schema.cnpj_emit, db=db)
            if not prod:
                continue
            if isinstance(prod, productSchemas.ProductResponse):
                result.append(
                    {
                        "product": prod,
                        "amount": i.q_com
                    }
                )
            elif isinstance(prod, compositionSchemas.CompositionResponse):
                for item in prod.items:
                    result.append(
                        {
                            "product": item.product,
                            "amount": i.q_com * item.amount_required
                        }
                    )
            


    return result




@router.post("/register-bank", response_model=finantialsSchemas.BankResponse)
def register_bank(
    bank: finantialsSchemas.BankCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)    
) -> finantialsSchemas.BankResponse:
    new_bank = finantialsModels.Bank(
        company_id=bank.company_id,
        bank_name=bank.bank_name,
        bank_code=bank.bank_code,
        agency=bank.agency,
        account_number=bank.account_number,
        account_digit=bank.account_digit,
        account_type=bank.account_type,
        holder_name=bank.holder_name,
        holder_document=bank.holder_document,
        is_active=bank.is_active,
        created_at=bank.created_at if bank.created_at else datetime.now(),
    )
    db.add(new_bank)
    db.commit()
    db.refresh(new_bank)
    return new_bank


@router.get("/banks")
def get_banks(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)   
):
    query = db.query(finantialsModels.Bank).all()
    return query
    

@router.get("/stock-position")
def get_stock_position(
    date: datetime,
    company_id: int,
    db: Session = Depends(get_db)   
):
    pb = finantialServices.PatrimonialBalance(company_id=company_id, date_begin=date - timedelta(days=1), date_end=date, db=db)
    pb._load_ativos()
    columns = [
            # "company_id",
            "sku",
            "name",
            # "picture",
            # "supplier_id",
            # "id",
            "last_entry_price",
            # "price_after_taxes",
            # "stock_unit_price",
            "stock",
            "virtual_stock",
            "available_stock",
            # "last_entry",
            # "last_sell",
            "stock_value",
            # "amount_sold",
    ]

    data = []
    for item in pb.ativo_circulante.detalhamento_estoque:
        data.append([
            # item.company_id,
            item.sku,
            item.name,
            # item.picture,
            # item.supplier_id,
            # item.id,
            item.last_entry_price,
            # item.price_after_taxes,
            # item.stock_unit_price,
            item.stock,
            item.virtual_stock,
            item.available_stock,
            # item.last_entry, 
            # item.last_sell,
            item.stock_value,
            # item.amount_sold,
        ])
    
    df = pd.DataFrame(columns=columns, data=data)

    filename = f"stock-{date.strftime('%Y-%m-%d')}.csv"
    try:
        df.to_csv(
            filename,
            index=False,
            encoding="utf-8-sig",
            sep=";",
            decimal=","
        )
    except PermissionError:
        pass

    return pb.ativo_circulante

@router.post("/upload-extract")
async def register_extract(
    company_id: int,
    bank_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    bank = finantialServices.Bank(bank_id=bank_id, db=db).get_bank()
    company = companyServices.Company(company_id=company_id, db=db).get_company()
    suppliers = db.query(suppliersModels.Suppliers).all()
    suppliers_cnpjs = [str(s.cnpj).replace("/", "").replace("-", "") for s in suppliers]

    contents = await file.read()
    excel = BytesIO(contents)

    models = []

    if bank.bank_name == "Itau":
        df = pd.read_excel(excel, skiprows=9)

        for _, row in df.iterrows():
            value = row.get("Valor (R$)")

            if pd.isna(value):
                continue

            model = finantialsModels.Transactions(
                company_id=company_id,
                bank_account_id=bank.id,
            )

            if value < 0:
                model.method = False
                model.value = abs(float(value))
            else:
                model.method = True
                model.value = float(value)

            model.counterparty_name = None if pd.isna(row.get("Lançamento")) else row.get("Lançamento")
            model.counterparty_document = None if pd.isna(row.get("CPF/CNPJ")) else row.get("CPF/CNPJ")
            model.destiny = None if pd.isna(row.get("Razão Social")) else row.get("Razão Social")
            model.transaction_date = row.get("Data")
            model.source = "itau"

            if str(model.counterparty_name).replace("/", "").replace("-", "") == company.cnpj:
                model.category = 5
            elif str(model.counterparty_name).replace("/", "").replace("-", "") in suppliers_cnpjs:
                model.category = 1
            
            elif 'RENDIMENTOS REND PAGO APLIC AUT MAIS' == str(model.counterparty_name):
                model.category = 10
            elif 'REND PAGO APLIC AUT MAIS' == str(model.counterparty_name):
                model.category = 10
            elif 'RENDIMENTOS REND PAGO APLIC AUT MAIS' == str(model.counterparty_name):
                model.category = 10
            
            
            
            db.add(model)
            db.commit()
            db.refresh(model)

            models.append(model)

        return models
    
    elif bank.bank_name == "Mercado Pago":
        read_options = {
            "skiprows": 2,
            "sep": ";",
            "decimal": ",",
            "thousands": ".",
            "dtype": {"REFERENCE_ID": str},
        }

        try:
            df = pd.read_csv(excel, encoding="utf-8-sig", **read_options)
        except UnicodeDecodeError:
            # Alguns extratos do Mercado Pago chegam codificados como Windows-1252.
            excel.seek(0)
            try:
                df = pd.read_csv(excel, encoding="cp1252", **read_options)
            except UnicodeDecodeError:
                # Latin-1 aceita bytes indefinidos no CP1252 (como 0x81), que
                # podem aparecer quando o arquivo é recodificado no upload.
                excel.seek(0)
                df = pd.read_csv(excel, encoding="latin-1", **read_options)

        df.columns = df.columns.str.strip()
        # print(df)


        for _, row in df.iterrows():
            try:
                reference_id = str(row["REFERENCE_ID"]).strip()
            except KeyError:
                reference_id = str(row["SOURCE_ID"]).strip()

            transaction_type = str(row["TRANSACTION_TYPE"]).strip()
            transaction_value = float(row["TRANSACTION_NET_AMOUNT"])

            query = (
                db.query(finantialsModels.Transactions)
                .filter(finantialsModels.Transactions.description == transaction_type)
            )

            category = query.first()
            if category:
                category = category.category

            query = query.filter(finantialsModels.Transactions.external_id == reference_id).first()

            if query:
                continue

            model = finantialsModels.Transactions(
                company_id=company_id,
                bank_account_id=bank.id,
                transaction_date=pd.to_datetime(row["RELEASE_DATE"], dayfirst=True),
                external_id=reference_id,
                description=transaction_type,
                source="mercado_pago"
            )


            model.counterparty_name = model.description


            if transaction_value > 0:
                model.method = True
                model.value = transaction_value
            else:
                model.method = False
                model.value = transaction_value * -1

            if category:
                model.category = category
            else:
                if 'Pagamento com Código QR Pix' in model.counterparty_name and model.method:
                    model.category = 9
                elif 'Pix recebido' in model.counterparty_name and model.method:
                    model.category = 9
                elif 'Liberação de dinheiro Venda' in model.counterparty_name and model.method:
                    model.category = 9
                elif 'Reembolso' in model.counterparty_name and model.method and 'DIFAL' not in model.counterparty_name:
                    model.category = 15
                elif 'canceled' in model.counterparty_name and not model.method:
                    model.category = 13
                elif 'Transferência Pix recebida' in model.counterparty_name and not model.method:
                    model.category = 9


            db.add(model)

        db.commit()


    elif bank.bank_name == 'Nubank':
        df = pd.read_csv(excel)

        # models = []
        for _, row in df.iterrows():
            query = db.query(finantialsModels.Transactions).filter(finantialsModels.Transactions.external_id == row['Identificador']).first()
            if query:
                continue
            model = finantialsModels.Transactions(
                company_id=company_id,
                bank_account_id=bank.id,
            )
            model.transaction_date = row['Data']
            model.external_id = row['Identificador']
            model.description = row['Descrição']
            model.counterparty_name = row['Descrição']

            if row['Valor'] > 0:
                model.method = True
                model.value = row['Valor']
            else:
                model.method = False
                model.value = row['Valor'] * (-1)
            db.add(model)
            db.commit()


@router.get("/get-extract")
def get_extract(
    company_id: int,
    bank_id: Optional[int] = None,
    category_id: Optional[int] = None,
    date_begin: Optional[datetime] = None,
    date_end: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    filters = [
        finantialsModels.Transactions.company_id == company_id
    ]

    if date_begin:
        filters.append(
            finantialsModels.Transactions.transaction_date >= date_begin
        )

    if date_end:
        filters.append(
            finantialsModels.Transactions.transaction_date <= date_end
        )

    if bank_id is not None:
        filters.append(
            finantialsModels.Transactions.bank_account_id == bank_id
        )

    if category_id is not None:
        filters.append(
            finantialsModels.Transactions.category == category_id
        )

    # filters.append(finantialsModels.Transactions.category.is_(None))

    # filters.append(
    #     or_(
    #         finantialsModels.Transactions.category.is_(None),
    #         finantialsModels.Transactions.category == 2
    #     )
    # )

    query = db.query(finantialsModels.Transactions).filter(*filters).order_by(finantialsModels.Transactions.transaction_date.desc()).all()

    return query


@router.put("/edit-transaction")
def update_transaction(
    new_transaction: finantialsSchemas.EditTransaction,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    print("new_transaction", new_transaction)
    query = db.query(finantialsModels.Transactions).filter(finantialsModels.Transactions.id == new_transaction.transaction_id).first()
    if not query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if new_transaction.counterparty_document:
        query.counterparty_document = new_transaction.counterparty_document

    db.commit()
    db.refresh(query)

    return query
    

@router.get("/categories")
def get_categories(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(finantialsModels.TransactionCategories).all()

@router.post("/create-categories", response_model=finantialsSchemas.TransactionCategoryResponse)
def create_category(
    category: finantialsSchemas.TransactionCategoryCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # evita criar categoria duplicada pelo nome
    exists = db.query(finantialsModels.TransactionCategories).filter(
        finantialsModels.TransactionCategories.category == category.name
    ).first()

    if exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Categoria já cadastrada"
        )

    new_category = finantialsModels.TransactionCategories(
        category=category.name,
    )

    db.add(new_category)
    db.commit()
    db.refresh(new_category)

    return {
        "id": new_category.id,
        "name": new_category.category
    }


@router.post("/attribute-payment")
def attribute_payment(
    attr: finantialsSchemas.AttributePayment,
    db: Session = Depends(get_db),
):
    print(attr.__dict__)
    transaction = db.query(finantialsModels.Transactions).filter(
        finantialsModels.Transactions.id == attr.transaction_id
    ).first()

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail="Transação não encontrada"
        )

    if attr.category_id:
        transaction.category = attr.category_id

    if not transaction.category:
        db.commit()
        db.refresh(transaction)

        return {
            "transaction": transaction,
            "has_motive": False,
            "motive": None,
            "message": "Transação sem categoria atribuída"
        }

    if attr.item_id:
        query = None

        if transaction.category == 1:
            query = db.query(suppliersModels.SupplierPayments).filter(
                suppliersModels.SupplierPayments.id == attr.item_id
            ).first()

            if query and hasattr(query, "transaction_id"):
                query.transaction_id = transaction.id
                query.data_pagamento = transaction.transaction_date

        elif transaction.category == 2:
            query = db.query(finantialsModels.Taxes).filter(
                finantialsModels.Taxes.id == attr.item_id
            ).first()

            if query:
                query.transaction_id = transaction.id
                query.payment_date = transaction.transaction_date

        elif transaction.category == 3:
            query = db.query(finantialsModels.Fixos).filter(
                finantialsModels.Fixos.id == attr.item_id
            ).first()

            if query:
                query.transaction_id = transaction.id

        elif transaction.category == 4:
            query = db.query(accountModels.EmployeePayroll).filter(
                accountModels.EmployeePayroll.id == attr.item_id
            ).first()

            if query:
                query.transaction_id = transaction.id
                query.data_pagamento = transaction.transaction_date
                query.paid = True
                if not query.data_competencia:
                    ultimo_dia = monthrange(
                        query.ano_referencia,
                        query.mes_referencia
                    )[1]
                    query.data_competencia = datetime(
                        year=query.ano_referencia,
                        month=query.mes_referencia,
                        day=ultimo_dia
                    )

        else:
            raise HTTPException(
                status_code=400,
                detail="Categoria inválida"
            )

        if not query:
            raise HTTPException(
                status_code=404,
                detail="Motivo/item não encontrado para essa categoria"
            )

        db.commit()
        db.refresh(transaction)
        db.refresh(query)

        return {
            "transaction": transaction,
            "has_motive": True,
            "motive": query
        }

    db.commit()
    db.refresh(transaction)

    search_result = search_item(
        transaction=transaction,
        db=db
    )

    return {
        "transaction": transaction,
        **search_result
    }
                
                

def normalize_date(value):
    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    if isinstance(value, str):
        return datetime.fromisoformat(value).date()

    return value


def search_item(
    transaction: finantialsModels.Transactions,
    db: Session
):
    if not transaction.category:
        return {
            "has_motive": False,
            "motive": None
        }

    transaction_date = normalize_date(transaction.transaction_date)

    def search_supplier(cnpj: str) -> int:
        try:
            cnpj = cnpj.replace("/", '').replace('-', '') 
        except:
            return None
        query = db.query(suppliersModels.Suppliers).filter(suppliersModels.Suppliers.cnpj == cnpj).first()
        if query:
            return query.id

    if transaction.category == 1:
        query = db.query(suppliersModels.SupplierPayments).filter(
            suppliersModels.SupplierPayments.valor == transaction.value
        ).filter(
            suppliersModels.SupplierPayments.company_id == transaction.company_id
        ).all()


        for item in query:
            item_date = normalize_date(item.vencimento)

            if hasattr(item, "transaction_id") and item.transaction_id == transaction.id:
                return {
                    "has_motive": True,
                    "motive": item
                }

            if hasattr(item, "transaction_id"):
                start_date = transaction_date - timedelta(days=3)
                end_date = transaction_date + timedelta(days=3)
                if item_date and not item.transaction_id and start_date <= item_date <= end_date:
                    return {
                        "has_motive": False,
                        "motive": item
                    }

        supplier = search_supplier(cnpj=transaction.counterparty_document)
        if not supplier:
            return {
            "has_motive": False,
            "motive": []
        }
        query = db.query(suppliersModels.SupplierPayments).filter(suppliersModels.SupplierPayments.transaction_id.is_(None))\
                .filter(suppliersModels.SupplierPayments.supplier_id == supplier).all()
        return {
            "has_motive": False,
            "motive": query
        }

    elif transaction.category == 2:
        query = db.query(finantialsModels.Taxes).filter(
            finantialsModels.Taxes.value == transaction.value
        ).all()

        for item in query:
            item_date = normalize_date(item.payment_date)

            if item.transaction_id == transaction.id:
                return {
                    "has_motive": True,
                    "motive": item
                }

            if not item.transaction_id and item_date == transaction_date:
                return {
                    "has_motive": False,
                    "motive": item
                }

        return {
            "has_motive": False,
            "motive": query
        }

    elif transaction.category == 3:
        query = db.query(finantialsModels.Fixos).filter(
            finantialsModels.Fixos.value == transaction.value
        ).all()

        for item in query:
            item_date = normalize_date(item.payment_date)

            if item.transaction_id == transaction.id:
                return {
                    "has_motive": True,
                    "motive": item
                }

            if not item.transaction_id and item_date == transaction_date:
                return {
                    "has_motive": False,
                    "motive": item
                }

        return {
            "has_motive": False,
            "motive": query
        }

    elif transaction.category == 4:
        cpf = str(transaction.counterparty_document).replace(".", "").replace("-", "")
        emp_query = db.query(accountModels.Employee).filter(accountModels.Employee.cpf == cpf).first()
        query = db.query(accountModels.EmployeePayroll).filter(
            accountModels.EmployeePayroll.salario_liquido == transaction.value
        )
        if emp_query:
            query = query.filter(accountModels.EmployeePayroll.employee_id == emp_query.id)
        query = query.all()

        for item in query:
            item_date = normalize_date(item.data_pagamento)
            item.items = item.items

            if item.transaction_id == transaction.id:
                return {
                    "has_motive": True,
                    "motive": item
                }

            if not item.transaction_id and item_date == transaction_date:
                return {
                    "has_motive": False,
                    "motive": item
                }

        return {
            "has_motive": False,
            "motive": query
        }

    return {
        "has_motive": False,
        "motive": []
    }
    
    
@router.get("/motives/{category_id}")
def get_motives(
    category_id: Optional[int] = None,
    date_begin: Optional[str] = None,
    date_end: Optional[str] = None,
    db: Session = Depends(get_db)
):
    if category_id:
        if category_id == 1:
            return {
                "category": "supplier"
            }

        elif category_id == 2:
            filter_params = []

            if date_begin:
                filter_params.append(finantialsModels.Taxes.payment_date >= date_begin)

            if date_end:
                filter_params.append(finantialsModels.Taxes.payment_date <= date_end)

            query = db.query(finantialsModels.Taxes).filter(*filter_params).all()


            return {
                "category": "taxes",
                "payments": query
            }

        elif category_id == 3:
            filter_params = []

            if date_begin:
                filter_params.append(finantialsModels.Fixos.payment_date >= date_begin)

            if date_end:
                filter_params.append(finantialsModels.Fixos.payment_date <= date_end)

            query = db.query(finantialsModels.Fixos).filter(*filter_params).all()

            return {
                "category": "fixos",
                "payments": query
            }

        elif category_id == 4:
            filter_params = []

            if date_begin:
                filter_params.append(accountModels.EmployeePayroll.data_vencimento >= date_begin)

            if date_end:
                filter_params.append(accountModels.EmployeePayroll.data_vencimento <= date_end)

            query = db.query(accountModels.EmployeePayroll).filter(*filter_params).all()

            return {
                "category": "folha_salarial",
                "payments": query
            }

        raise HTTPException(
            status_code=400,
            detail="Categoria inválida"
        )


@router.get("/duplicated")
def get_duplicated_invoices():
    url = f"{API_URL}/invoices"
    params = {
        "cnpj": "43861450000181",
        "emit": True,
        "events": True,
        "date_begin": "2026-06-03"
    }

    req = requests.get(url=url, timeout=30, params=params)

    if req.status_code != 200:
        return {
            "error": True,
            "status_code": req.status_code,
            "message": req.text
        }

    data = req.json()

    result = {}

    for item in data["invoices"]:
        cpf_dest = item["cnpj_dest"]

        invoice = {
            "chave": item["chave_acesso"],
            "valor": item["v_nf"],
            "numero": item["numero"],
            "serie": item["serie"],
            "dh_emit": item["dh_emissao"],
            "events": item["events"],
            "duplicated": False
        }

        if cpf_dest not in result:
            result[cpf_dest] = []

        result[cpf_dest].append(invoice)

    result_2 = {}
    chaves = []

    for cpf_dest, notas in result.items():
        if len(notas) <= 1:
            continue

        last_value = None
        serie = None
        chave = None

        for nota in notas:
            if last_value is None and serie is None:
                last_value = nota["valor"]
                serie = nota["serie"]
                chave = nota["chave"]
            else:
                if last_value == nota["valor"] and serie != nota["serie"]:
                    nota["duplicated"] = True
                    chaves.append(chave)

    for cpf, notas in result.items():
        for nota in notas:
            if nota["chave"] in chaves:
                nota["duplicated"] = True

    for cpf, notas in result.items():
        for nota in notas:
            if nota["duplicated"]:
                if cpf not in result_2:
                    result_2[cpf] = []

                result_2[cpf].append(nota)

    rows = []

    for cpf, notas in result_2.items():
        for nota in notas:
            rows.append({
                "cnpj_dest": cpf,
                "chave": nota["chave"],
                "valor": nota["valor"],
                "numero": nota["numero"],
                "serie": nota["serie"],
                "dh_emit": nota["dh_emit"],
                "duplicated": nota["duplicated"],
                "events": str(nota["events"])
            })

    df = pd.DataFrame(rows)

    df.to_excel("duplicated_invoices.xlsx", index=False)
    # df.to_excel("duplicated_invoices.xlsx", index=False, encoding="utf-8-sig")

    # return {
    #     "total": len(rows),
    #     "csv": "duplicated_invoices.csv",
    #     "data": result_2
    # }

    return result_2
