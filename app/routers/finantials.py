from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends, UploadFile, File, Query
from ..schemas import finantialsSchemas, productSchemas, compositionSchemas
from ..models import finantialsModels, suppliersModels, identificatorsModels
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

@router.get("/balance")
def get_balance(
    company_id: int,
    date_begin: date,
    date_end: date,
    show_details: Optional[bool] = False,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return finantialServices.PatrimonialBalance(
        company_id=company_id,
        date_begin=date_begin,
        date_end=date_end,
        db=db
    ).get_balance(show_details=show_details)

@router.get("/dre")
def get_dre(
    company_id: int,
    date_begin: date,
    date_end: date,
    show_details: Optional[bool] = False,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return finantialServices.Dre(
        company_id=company_id,
        date_begin=date_begin,
        date_end=date_end,
        db=db
    ).get_dre(show_details=show_details)



@router.get("/fix-stock")
def fix_stock(
    company_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    company = companyServices.Company(company_id=company_id, db=db).get_company()

    suppliers = db.query(suppliersModels.Suppliers).all()
    sup_cnpjs = [s.cnpj for s in suppliers]


    d_begin = '2025-12-01'

    compras = get_invoices(cnpj=company.cnpj, date_begin=d_begin)['invoices']
    vendas = get_invoices(cnpj=company.cnpj, date_begin=d_begin, emit=True)['invoices']


    result = []
    for c in compras:
        nf_schema = finantialsSchemas.InvoiceBase.model_validate(c)
        for i in nf_schema.items:
            prod = get_product_by_cprod(c_prod=i.c_prod, sup_cnpj=nf_schema.cnpj_emit, db=db)
            if not prod:
                continue
            if isinstance(prod, productSchemas.ProductResponse):
                result.append(
                    {
                        "data": nf_schema.dh_emissao,
                        "product": prod,
                        "amount": i.q_com
                    }
                )
            elif isinstance(prod, compositionSchemas.CompositionResponse):
                for item in prod.items:
                    result.append(
                        {
                            "data": nf_schema.dh_emissao,
                            "product": item.product,
                            "amount": i.q_com / item.amount_required
                        }
                    )


    from .products import search_by_sku
    for v in vendas:
        nf_schema = finantialsSchemas.InvoiceBase.model_validate(v)
        for i in nf_schema.items:
            prod = search_by_sku(sku=i.c_prod, db=db, refresh=False)
            if isinstance(prod, productSchemas.ProductResponse):
                result.append(
                    {
                        "data": nf_schema.dh_emissao,
                        "product": prod,
                        "amount": (i.q_com) * (-1)
                    }
                )
            elif isinstance(prod, compositionSchemas.CompositionResponse):
                for item in prod.items:
                    result.append(
                        {
                            "data": nf_schema.dh_emissao,
                            "product": item.product,
                            "amount": (i.q_com / item.amount_required) * (-1)
                        }
                    )


    return process_result(result)
            

def process_result(data):
    result = {}
    for item in data:
        raw_date = item["data"]

        if isinstance(raw_date, datetime):
            only_date = raw_date.date()
        elif isinstance(raw_date, date):
            only_date = raw_date
        elif isinstance(raw_date, str):
            only_date = datetime.fromisoformat(raw_date).date()
        else:
            raise TypeError(f"Tipo inválido para data: {type(raw_date)} - valor: {raw_date}")

        if only_date not in result:
            result[only_date] = [
                {
                    "sku": item["product"].sku,
                    "pid": item["product"].id,
                    "amount": item["amount"]
                }
            ]
        else:
            result[only_date].append(
                {
                    "sku": item["product"].sku,
                    "pid": item["product"].id,
                    "amount": item["amount"]
                }
            )

    final_result = {}
    for day in result:
        final_result[day] = sum_quantities(result[day])





    return final_result


def sum_quantities(data):
    result = {}
    for item in data:
        if item['sku'] not in result:
            result[item['sku']] = item
        else:
            result[item['sku']]['amount'] += item['amount']

    return result


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
    new_bank = finantialsModels.DimBankAccounts(
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