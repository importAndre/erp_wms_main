from fastapi import APIRouter, Depends, HTTPException, status
import requests
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, distinct
from ..models import accountModels, suppliersModels, identificatorsModels, productModels, compositionModels
from ..schemas import supplierSchemas, finantialsSchemas
from ..database import get_db
from ..oauth2 import get_current_user
from ..services import userServices, supplierServices, companyServices, productServices, compositionServices
from datetime import datetime
from typing import List, Optional, Union
from ..server_config import API_URL


router = APIRouter(
    prefix="/suppliers",
    tags=["suppliers"],
    responses={404: {"description": "Not found"}},
)


def _parse_optional_datetime(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _parse_optional_float(value):
    if value is None:
        return None
    try:
        return float(str(value).replace(",", "."))
    except ValueError:
        return None


def _get_payment_installments(nf: supplierSchemas.SupplierPaymentsBase):
    if not nf.pagamentos:
        return []

    dups = nf.pagamentos.dup or []
    installments = []

    for dup in dups:
        if not dup.nDup:
            continue

        try:
            parcela = int(dup.nDup)
        except (TypeError, ValueError):
            continue

        installments.append({
            "parcela": parcela,
            "valor": _parse_optional_float(dup.vDup),
            "vencimento": _parse_optional_datetime(dup.dVenc),
        })

    if installments:
        quantidade_parcelas = len(installments)
        for installment in installments:
            installment["quantidade_parcelas"] = quantidade_parcelas
        return installments

    det_pag = nf.pagamentos.detPag
    if det_pag and det_pag.indPag == "0":
        return [{
            "parcela": 1,
            "quantidade_parcelas": 1,
            "valor": _parse_optional_float(det_pag.vPag),
            "vencimento": nf.date_emit,
        }]

    return []

def _validate_supplier_order_references(
    db: Session,
    company_id: int,
    supplier_internal_code: str,
    items,
):
    if not db.query(accountModels.Company.id).filter(
        accountModels.Company.id == company_id
    ).first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa não encontrada",
        )

    if not db.query(suppliersModels.Suppliers.id).filter(
        suppliersModels.Suppliers.internal_code == supplier_internal_code
    ).first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fornecedor não encontrado pelo código interno informado",
        )

    product_ids = {item.product_id for item in items if item.product_id is not None}
    composition_ids = {
        item.composition_id for item in items if item.composition_id is not None
    }
    existing_product_ids = {
        row[0]
        for row in db.query(productModels.Product.id).filter(
            productModels.Product.id.in_(product_ids),
            productModels.Product.company_id == company_id,
        ).all()
    } if product_ids else set()
    missing_product_ids = product_ids - existing_product_ids
    if missing_product_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Produtos não encontrados na empresa: {sorted(missing_product_ids)}",
        )

    existing_composition_ids = {
        row[0]
        for row in db.query(compositionModels.Composition.id).filter(
            compositionModels.Composition.id.in_(composition_ids),
            compositionModels.Composition.company_id == company_id,
        ).all()
    } if composition_ids else set()
    missing_composition_ids = composition_ids - existing_composition_ids
    if missing_composition_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Composições não encontradas na empresa: "
                f"{sorted(missing_composition_ids)}"
            ),
        )


@router.post("/create", response_model=supplierSchemas.SupplierResponse)
def create_supplier(
    supplier: supplierSchemas.SupplierCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = userServices.User(user=current_user, db=db)
    user.check_users_permission(task='create_supplier')
    supplier.cnpj = supplier.cnpj.replace("/", "").replace("-", '')
    # print(supplier.cnpj)
    
    new_supplier = suppliersModels.Suppliers(
        internal_code=supplier.internal_code,
        cnpj=supplier.cnpj,
        razao_social=supplier.razao_social,
        nome_fantasia=supplier.nome_fantasia,
        data_abertura=supplier.data_abertura,
        natureza_juridica=supplier.natureza_juridica,
        situacao=supplier.situacao,
        situacao_especial=supplier.situacao_especial,
        tipo_unidade=supplier.tipo_unidade,
        enquadramento_de_porte=supplier.enquadramento_de_porte,
        capital_social=supplier.capital_social,
        opcao_pelo_mei=supplier.opcao_pelo_mei,
        opcao_pelo_simples=supplier.opcao_pelo_simples,
        inscricao_estadual=supplier.inscricao_estadual
    )

    db.add(new_supplier)
    db.commit()
    db.refresh(new_supplier)

    return new_supplier



@router.get("/all", response_model=List[supplierSchemas.SupplierResponse])
def get_all(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(suppliersModels.Suppliers).all()
    return [supplierServices.Supplier(supplier=s, db=db).get_supplier() for s in query]
    


@router.get("/get/{sid}", response_model=supplierSchemas.SupplierResponse)
def get_supplier(
    sid: Optional[int] = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
) -> supplierSchemas.SupplierResponse:
    return supplierServices.Supplier(sid=sid, db=db).get_supplier()


@router.post(
    "/orders",
    response_model=supplierSchemas.SupplierOrderResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_supplier_order(
    order: supplierSchemas.SupplierOrderCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _validate_supplier_order_references(
        db=db,
        company_id=order.company_id,
        supplier_internal_code=order.supplier_internal_code,
        items=order.items,
    )

    order_data = order.model_dump(exclude={"items"})
    new_order = suppliersModels.SupplierOrders(**order_data)
    new_order.items = [
        suppliersModels.SupplierOrderItems(**item.model_dump())
        for item in order.items
    ]

    try:
        db.add(new_order)
        db.commit()
        db.refresh(new_order)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não foi possível registrar o pedido do fornecedor",
        ) from exc

    return new_order


@router.get(
    "/orders",
    response_model=List[supplierSchemas.SupplierOrderResponse],
)
def list_supplier_orders(
    company_id: int,
    supplier_internal_code: Optional[str] = None,
    date_begin: Optional[datetime] = None,
    date_end: Optional[datetime] = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(suppliersModels.SupplierOrders).options(
        selectinload(suppliersModels.SupplierOrders.items)
    ).filter(suppliersModels.SupplierOrders.company_id == company_id)

    if supplier_internal_code:
        query = query.filter(
            suppliersModels.SupplierOrders.supplier_internal_code
            == supplier_internal_code
        )
    if date_begin:
        query = query.filter(suppliersModels.SupplierOrders.created_at >= date_begin)
    if date_end:
        query = query.filter(suppliersModels.SupplierOrders.created_at <= date_end)

    return query.order_by(suppliersModels.SupplierOrders.created_at.desc()).all()


@router.get(
    "/orders/{order_id}",
    response_model=supplierSchemas.SupplierOrderResponse,
)
def get_supplier_order(
    order_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = db.query(suppliersModels.SupplierOrders).options(
        selectinload(suppliersModels.SupplierOrders.items)
    ).filter(suppliersModels.SupplierOrders.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido do fornecedor não encontrado",
        )
    return order


@router.patch(
    "/orders/{order_id}",
    response_model=supplierSchemas.SupplierOrderResponse,
)
def update_supplier_order(
    order_id: int,
    update: supplierSchemas.SupplierOrderUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = db.query(suppliersModels.SupplierOrders).options(
        selectinload(suppliersModels.SupplierOrders.items)
    ).filter(suppliersModels.SupplierOrders.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido do fornecedor não encontrado",
        )

    update_data = update.model_dump(exclude_unset=True, exclude={"items"})
    required_fields = {"company_id", "supplier_internal_code", "arrived_percent"}
    null_required_fields = sorted(
        field
        for field in required_fields
        if field in update_data and update_data[field] is None
    )
    if null_required_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Os campos {', '.join(null_required_fields)} não podem ser nulos",
        )

    company_id = update_data.get("company_id", order.company_id)
    supplier_internal_code = update_data.get(
        "supplier_internal_code",
        order.supplier_internal_code,
    )
    items = update.items if update.items is not None else order.items
    _validate_supplier_order_references(
        db=db,
        company_id=company_id,
        supplier_internal_code=supplier_internal_code,
        items=items,
    )

    if update.items is not None:
        existing_items = {item.id: item for item in order.items}
        requested_existing_ids = {
            item.id for item in update.items if item.id is not None
        }
        invalid_item_ids = requested_existing_ids - set(existing_items)
        if invalid_item_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Itens não pertencem ao pedido informado: "
                    f"{sorted(invalid_item_ids)}"
                ),
            )

        updated_items = []
        for item_data in update.items:
            values = item_data.model_dump(exclude={"id"})
            if item_data.id is None:
                item = suppliersModels.SupplierOrderItems(**values)
            else:
                item = existing_items[item_data.id]
                for field, value in values.items():
                    setattr(item, field, value)
            updated_items.append(item)
        order.items = updated_items

    for field, value in update_data.items():
        setattr(order, field, value)

    try:
        db.commit()
        db.refresh(order)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não foi possível atualizar o pedido do fornecedor",
        ) from exc

    return order



@router.get("/payments", response_model=supplierSchemas.SupplierPaymentsResponse)
def get_payments(
    supplier_id: Optional[int] = None,
    company_id: Optional[int] = None,
    date_begin: Optional[str] = None,
    date_end: Optional[str] = None,
    chave_acesso: Optional[str] = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    register_payments(current_user=current_user, db=db)

    # Nas listagens comuns, mostra apenas parcelas a vencer. Uma busca por chave
    # precisa localizar a nota independentemente do vencimento.
    filter_params = []
    if chave_acesso is None:
        filter_params.append(
            suppliersModels.SupplierPayments.vencimento >= datetime.now()
        )
    if supplier_id is not None:
        filter_params.append(suppliersModels.SupplierPayments.supplier_id == supplier_id)
    if company_id is not None:
        filter_params.append(suppliersModels.SupplierPayments.company_id == company_id)
    if date_begin is not None:
        filter_params.append(suppliersModels.SupplierPayments.vencimento >= date_begin)
    if date_end is not None:
        filter_params.append(suppliersModels.SupplierPayments.vencimento <= date_end)
    if chave_acesso is not None:
        filter_params.append(suppliersModels.SupplierPayments.chave_acesso == chave_acesso)

    base_query = db.query(suppliersModels.SupplierPayments).filter(*filter_params)\
            .order_by(suppliersModels.SupplierPayments.vencimento.desc()).all()
    result = supplierSchemas.SupplierPaymentsResponse()
    result.quantidade_pagamentos = len(base_query)

    notas_pendentes = []
    for p in base_query:
        payment = supplierSchemas.Payments()
        result.total += p.valor

        payment.id = p.id
        payment.company_id = p.company_id
        payment.supplier_id = p.supplier_id
        payment.transaction_id = p.transaction_id
        payment.chave_acesso = p.chave_acesso
        payment.numero_nota = p.numero_nota
        payment.parcela = p.parcela
        payment.quantidade_parcelas = p.quantidade_parcelas
        payment.valor = p.valor
        payment.vencimento = p.vencimento
        payment.date_emit = p.date_emit
        payment.data_pagamento = p.data_pagamento
        payment.supplier = supplierServices.Supplier(sid=p.supplier_id, db=db).get_supplier()
        
        result.payments.append(payment)

        if p.chave_acesso in notas_pendentes:
            pass
        else:
            notas_pendentes.append(p.chave_acesso)

    
    result.notas_pendentes = len(notas_pendentes)

    return result





@router.post(
    "/payments/manual",
    response_model=Union[supplierSchemas.SupplierPaymentManualResponse, List[supplierSchemas.SupplierPaymentManualResponse]],
    status_code=status.HTTP_201_CREATED
)
def register_supplier_payment_manual(
    payment: supplierSchemas.SupplierPaymentManualCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    company = db.query(accountModels.Company).filter(
        accountModels.Company.id == payment.company_id
    ).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa não encontrada"
        )

    supplier = db.query(suppliersModels.Suppliers).filter(
        suppliersModels.Suppliers.id == payment.supplier_id
    ).first()
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fornecedor não encontrado"
        )

    if payment.parcela > payment.quantidade_parcelas:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A parcela não pode ser maior que a quantidade de parcelas"
        )

    new_payment = suppliersModels.SupplierPayments(**payment.model_dump())

    try:
        db.add(new_payment)
        db.commit()
        db.refresh(new_payment)
    except IntegrityError:
        db.rollback()
        # return db.query(suppliersModels.SupplierPayments).filter(suppliersModels.SupplierPayments.chave_acesso == payment.chave_acesso).all()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um pagamento com esta empresa, chave de acesso e parcela"
        )
    except Exception:
        db.rollback()
        raise

    return new_payment


@router.patch(
    "/payments/{payment_id}",
    response_model=supplierSchemas.SupplierPaymentManualResponse
)
def update_supplier_payment(
    payment_id: int,
    payload: supplierSchemas.SupplierPaymentUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    print(payload)
    payment = db.query(suppliersModels.SupplierPayments).filter(
        suppliersModels.SupplierPayments.id == payment_id
    ).first()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pagamento não encontrado"
        )

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Informe ao menos um campo para atualizar"
        )

    required_fields = {
        "company_id",
        "supplier_id",
        "chave_acesso",
        "numero_nota"
    }
    null_required_fields = [
        field for field in required_fields
        if field in update_data and update_data[field] is None
    ]
    if null_required_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Os campos {', '.join(sorted(null_required_fields))} "
                "não podem ser nulos"
            )
        )

    company_id = update_data.get("company_id", payment.company_id)
    company = db.query(accountModels.Company).filter(
        accountModels.Company.id == company_id
    ).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa não encontrada"
        )

    supplier_id = update_data.get("supplier_id", payment.supplier_id)
    if supplier_id is not None:
        supplier = db.query(suppliersModels.Suppliers).filter(
            suppliersModels.Suppliers.id == supplier_id
        ).first()
        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Fornecedor não encontrado"
            )

    parcela = update_data.get("parcela", payment.parcela)
    quantidade_parcelas = update_data.get(
        "quantidade_parcelas",
        payment.quantidade_parcelas
    )
    if (
        parcela is not None
        and quantidade_parcelas is not None
        and parcela > quantidade_parcelas
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A parcela não pode ser maior que a quantidade de parcelas"
        )

    for field, value in update_data.items():
        setattr(payment, field, value)

    try:
        db.commit()
        db.refresh(payment)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um pagamento com esta empresa, chave de acesso e parcela"
        )
    except Exception:
        db.rollback()
        raise

    return payment



def register_payments(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = userServices.User(user=current_user, db=db)
    companies = user.companies
    result = {}

    for comp in companies:
        url = f"{API_URL}/invoices/payments/?cnpj={comp.cnpj}"
        # params = {"emit": False}
        # req = requests.get(url=url, timeout=30, params=params)
        req = requests.get(url=url, timeout=30)

        if req.status_code != 200:
            result[comp.nome_fantasia] = {"ok": False, "status_code": req.status_code}
            continue

        payload = supplierSchemas.GetSupplierPayment.model_validate(req.json())
        inserted = 0
        skipped = 0

        for nf in payload.payments:
            installments = _get_payment_installments(nf)

            if not nf.chave_acesso or not installments:
                continue

            cnpj_emit = nf.cnpj_emit

            try:
                supplier = supplierServices.Supplier(cnpj=cnpj_emit, db=db).get_supplier()
            except AttributeError:
                # print(f"CNPJ not found: {cnpj_emit}")
                continue

            for installment in installments:
                exists = (
                    db.query(suppliersModels.SupplierPayments)
                    .filter(
                        suppliersModels.SupplierPayments.company_id == comp.id,
                        suppliersModels.SupplierPayments.chave_acesso == nf.chave_acesso,
                        suppliersModels.SupplierPayments.parcela == installment["parcela"],
                    )
                    .first()
                )

                if exists:
                    # print("exists", nf.numero_nota)
                    updated = False
                    if exists.quantidade_parcelas != installment["quantidade_parcelas"]:
                        exists.quantidade_parcelas = installment["quantidade_parcelas"]
                        updated = True
                    if supplier and exists.supplier_id != supplier.id:
                        exists.supplier_id = supplier.id
                        updated = True
                    if not exists.numero_nota:
                        exists.numero_nota = nf.numero_nota
                        updated = True
                    if not exists.date_emit:
                        # print("here", nf.date_emit)
                        exists.date_emit = nf.date_emit
                        updated = True
                    if updated:
                        db.add(exists)

                    skipped += 1
                    continue

                # print("not exists", nf.numero_nota)
                new_entry = suppliersModels.SupplierPayments(
                    company_id=comp.id,
                    supplier_id=supplier.id,
                    chave_acesso=nf.chave_acesso,
                    numero_nota=nf.numero_nota,
                    parcela=installment["parcela"],
                    quantidade_parcelas=installment["quantidade_parcelas"],
                    valor=installment["valor"],
                    vencimento=installment["vencimento"],
                    date_emit=nf.date_emit
                )
                db.add(new_entry)
                inserted += 1

        db.commit()
        result[comp.nome_fantasia] = {
            "ok": True,
            "inserted": inserted,
            "skipped_existing": skipped
        }

    return result



@router.get("/product")
def get_supplier_product(
    cprod: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    url = f"{API_URL}/invoices/product"
    params = {"cprod": cprod}
    req = requests.get(url=url, params=params)
    if req.status_code == 200:
        return req.json()
    return {"message": f"{cprod} not found in database."}


NOT_REGISTERED = None

@router.get("/not-registered")
def get_not_registered(
    company_id: Optional[int] = 1,
    refresh: Optional[bool] = False,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    global NOT_REGISTERED
    if not refresh and NOT_REGISTERED:
        return NOT_REGISTERED

    company = companyServices.Company(company_id=company_id, db=db).get_company()

    def get_registered_supplier_codes(company_id: int):
        params = [
            identificatorsModels.Identificators.company_id == company_id,
            identificatorsModels.Identificators.identif_type == "supplier_code",
        ]
        identifs = db.query(identificatorsModels.Identificators).filter(*params).all()

        registered_supplier_codes = set()

        for ident in identifs:
            try:
                if ident.is_composition:
                    comp = compositionServices.Composition(
                        cid=ident.composition_id,
                        db=db
                    ).get_composition()

                    if (
                        comp
                        and comp.items
                        and comp.items[0].product
                        and comp.items[0].product.supplier
                        and comp.items[0].product.supplier.cnpj
                    ):
                        cnpj = comp.items[0].product.supplier.cnpj
                        registered_supplier_codes.add((cnpj, ident.value))

                else:
                    prod = productServices.Product(
                        pid=ident.product_id,
                        db=db
                    ).get_product()

                    if prod and prod.supplier and prod.supplier.cnpj:
                        cnpj = prod.supplier.cnpj
                        registered_supplier_codes.add((cnpj, ident.value))
            except Exception:
                # se quiser, pode logar aqui
                continue

        return registered_supplier_codes

    def get_registered_purchases(company_id: int):
        purchases = (
            db.query(suppliersModels.Purchases)
            .filter(suppliersModels.Purchases.company_id == company_id)
            .all()
        )

        registered_purchases = set()

        for p in purchases:
            # TROQUE p.c_prod pelo nome real do campo na sua tabela Purchases
            # Ex.: p.product_code, p.supplier_code, etc.
            c_prod = getattr(p, "c_prod", None)

            if p.seller_cnpj and c_prod and p.invoice_id:
                registered_purchases.add((p.seller_cnpj, c_prod, p.invoice_id))

        return registered_purchases

    url = f"{API_URL}/invoices"
    params = {
        "cnpj": company.cnpj,
        "emit": False
    }

    req = requests.get(url=url, timeout=30, params=params)

    if req.status_code != 200:
        return {
            "error": "Não foi possível consultar as notas",
            "status_code": req.status_code
        }

    registered_supplier_codes = get_registered_supplier_codes(company_id=company_id)
    registered_purchases = get_registered_purchases(company_id=company_id)

    data = req.json()
    result = []

    for item in data.get("invoices", []):
        invoice = finantialsSchemas.InvoiceBase.model_validate(item)

        invoice_id = invoice.id
        seller_cnpj = invoice.cnpj_emit

        if not seller_cnpj or not invoice.items:
            continue

        missing_items = []

        for inv_item in invoice.items:
            c_prod = inv_item.c_prod

            if not c_prod:
                continue

            has_supplier_code = (seller_cnpj, c_prod) in registered_supplier_codes
            has_purchase = (seller_cnpj, c_prod, invoice_id) in registered_purchases

            if not has_supplier_code or not has_purchase:
                missing_items.append({
                    "invoice_id": invoice_id,
                    "numero": invoice.numero,
                    "serie": invoice.serie,
                    "cnpj_emit": seller_cnpj,
                    "c_prod": c_prod,
                    "x_prod": inv_item.x_prod,
                    "supplier_code_registered": has_supplier_code,
                    "purchase_registered": has_purchase,
                })

        if missing_items:
            result.append({
                "invoice_id": invoice_id,
                "numero": invoice.numero,
                "serie": invoice.serie,
                "cnpj_emit": seller_cnpj,
                "dh_emissao": invoice.dh_emissao,
                "items_not_registered": missing_items
            })

    NOT_REGISTERED = result
    print(len(result))
    return result
    
    

@router.post("/register-purchase", response_model=supplierSchemas.PurchaseResponse)
def register_purchase(
    purchase: supplierSchemas.PurchaseCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if purchase.numero_nota:
        company = companyServices.Company(company_id=purchase.company_id, db=db).get_company()
        url = f"{API_URL}/invoices/product"
        params = {
            "cprod": purchase.c_prod,
            "supplier_cnpj": purchase.seller_cnpj,
            "buyer_cnpj": company.cnpj,
            "numero": purchase.numero_nota
            }
        req = requests.get(url=url, params=params)
        if req.status_code == 200:
            data = req.json()
            # return data
            invoice = finantialsSchemas.InvoiceBase.model_validate(data['invoice'])
            item = finantialsSchemas.InvoiceItemBase.model_validate(data['item'])
        
            new_purchase = suppliersModels.Purchases(
                company_id=purchase.company_id,
                user_id=current_user.id,
                invoice_id=invoice.id,
                category=purchase.category,
                asset_name=purchase.asset_name,
                c_prod=purchase.c_prod,
                seller_cnpj=purchase.seller_cnpj,
                quantity=item.q_com,
                unit_value=item.v_un_com,
                total_value=item.v_prod,
                purchase_date=invoice.dh_emissao
            )
            db.add(new_purchase)
            db.commit()
            db.refresh(new_purchase)
            return new_purchase

    else:
        if not purchase.total_value:
            purchase.total_value = purchase.unit_value * purchase.quantity
        new_purchase = suppliersModels.Purchases(
                company_id=purchase.company_id,
                user_id=current_user.id,
                # invoice_id=,
                category=purchase.category,
                asset_name=purchase.asset_name,
                c_prod=purchase.c_prod,
                seller_cnpj=purchase.seller_cnpj,
                quantity=purchase.quantity,
                unit_value=purchase.unit_value,
                total_value=purchase.total_value,
                purchase_date=purchase.purchase_date
            )
        db.add(new_purchase)
        db.commit()
        db.refresh(new_purchase)
        return new_purchase


    return {"message": f"{purchase.cprod} not found in database."}

from datetime import datetime, date, time
from typing import Optional, List
from fastapi import Depends, Query
from sqlalchemy.orm import Session


@router.get("/purchases", response_model=List[supplierSchemas.PurchaseResponse])
def get_purchases(
    company_id: int,
    date_begin: Optional[date] = Query(None),
    date_end: Optional[date] = Query(None),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    query = db.query(suppliersModels.Purchases).filter(
        suppliersModels.Purchases.company_id == company_id
    )

    if date_begin:
        date_begin_datetime = datetime.combine(date_begin, time.min)

        query = query.filter(
            suppliersModels.Purchases.purchase_date >= date_begin_datetime
        )

    if date_end:
        date_end_datetime = datetime.combine(date_end, time.max)

        query = query.filter(
            suppliersModels.Purchases.purchase_date <= date_end_datetime
        )

    if category:
        query = query.filter(
            suppliersModels.Purchases.category == category
        )

    purchases = query.order_by(
        suppliersModels.Purchases.purchase_date.desc()
    ).all()

    return purchases

@router.get("/stock-value", response_model=Union[supplierSchemas.SupplierProductsResponse, List[supplierSchemas.SupplierProductsResponse]])
def get_stock_value(
    supplier_id: Optional[int] = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if supplier_id:
        return supplierServices.Supplier(sid=supplier_id, db=db).get_supplier_products()
    query = db.query(suppliersModels.Suppliers).all()
    return [supplierServices.Supplier(sid=item.id, db=db).get_supplier_products() for item in query]


@router.get("/products/{internal_code}")
def get_products(
    internal_code: str,
    date_begin: Optional[datetime] = None,
    date_end: Optional[datetime] = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from .products import product_sales
    suppliers = db.query(suppliersModels.Suppliers).filter(suppliersModels.Suppliers.internal_code == internal_code).all()
    sup_ids = [s.id for s in suppliers]

    products = db.query(productModels.Product).filter(productModels.Product.supplier_id.in_(sup_ids))
    result = []
    for p in products:
        # print(p.sku)
        result.append(
            product_sales(
                company_id=p.company_id,
                product_id=[p.id],
                date_begin=date_begin,
                date_end=date_end,
                current_user=current_user,
                db=db
            )
        )
    return result
