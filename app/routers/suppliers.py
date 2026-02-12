from fastapi import APIRouter, Depends, HTTPException, status
import requests
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from ..models import suppliersModels
from ..schemas import supplierSchemas
from ..database import get_db
from ..oauth2 import get_current_user
from ..services import userServices, supplierServices
from datetime import datetime
from typing import List, Optional
from ..server_config import API_URL


router = APIRouter(
    prefix="/suppliers",
    tags=["suppliers"],
    responses={404: {"description": "Not found"}},
)

@router.post("/create", response_model=supplierSchemas.SupplierResponse)
def create_supplier(
    supplier: supplierSchemas.SupplierCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = userServices.User(user=current_user, db=db)
    user.check_users_permission(task='create_supplier')
    
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



@router.get("/payments", response_model=supplierSchemas.SupplierPaymentsResponse)
def get_payments(
    supplier_id: Optional[int] = None,
    company_id: Optional[int] = None,
    date_begin: Optional[str] = None,
    date_end: Optional[str] = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    register_payments(current_user=current_user, db=db)

    today = datetime.now()

    # Base: parcelas a vencer/vencendo daqui pra frente (igual sua regra atual)
    filter_params = [suppliersModels.SupplierPayments.vencimento >= today]
    if supplier_id is not None:
        filter_params.append(suppliersModels.SupplierPayments.supplier_id == supplier_id)
    if company_id is not None:
        filter_params.append(suppliersModels.SupplierPayments.company_id == company_id)
    if date_begin is not None:
        filter_params.append(suppliersModels.SupplierPayments.vencimento >= date_begin)
    if date_end is not None:
        filter_params.append(suppliersModels.SupplierPayments.vencimento <= date_end)

    base_query = db.query(suppliersModels.SupplierPayments).filter(*filter_params)\
            .order_by(suppliersModels.SupplierPayments.vencimento.desc()).all()
    result = supplierSchemas.SupplierPaymentsResponse()
    result.quantidade_pagamentos = len(base_query)

    notas_pendentes = []
    for p in base_query:
        payment = supplierSchemas.Payments()
        result.total += p.valor

        payment.parcela = p.parcela
        payment.quantidade_parcelas = p.quantidade_parcelas
        payment.valor = p.valor
        payment.vencimento = p.vencimento
        payment.supplier = supplierServices.Supplier(sid=p.supplier_id, db=db).get_supplier()
        
        result.payments.append(payment)

        if p.chave_acesso in notas_pendentes:
            pass
        else:
            notas_pendentes.append(p.chave_acesso)

    
    result.notas_pendentes = len(notas_pendentes)

    return result



def register_payments(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = userServices.User(user=current_user, db=db)
    companies = user.companies
    result = {}

    for comp in companies:
        url = f"{API_URL}/invoices/payments/?cnpj={comp.cnpj}"
        req = requests.get(url=url, timeout=30)

        if req.status_code != 200:
            result[comp.nome_fantasia] = {"ok": False, "status_code": req.status_code}
            continue

        payload = supplierSchemas.GetSupplierPayment.model_validate(req.json())
        inserted = 0
        skipped = 0

        for nf in payload.payments:
            if not nf.pagamentos:
                continue

            dups = nf.pagamentos.dup or []
            if isinstance(dups, dict):
                dups = [dups]

            if not nf.chave_acesso or not dups:
                continue

            quantidade_parcelas = len(dups)
            cnpj_emit = nf.cnpj_emit

            try:
                supplier = supplierServices.Supplier(cnpj=cnpj_emit, db=db).get_supplier()
            except AttributeError:
                print(f"CNPJ not found: {cnpj_emit}")
                continue

            for dup in dups:
                if not dup.nDup:
                    continue

                try:
                    parcela_int = int(dup.nDup)
                except (TypeError, ValueError):
                    continue

                exists = (
                    db.query(suppliersModels.SupplierPayments)
                    .filter(
                        suppliersModels.SupplierPayments.company_id == comp.id,
                        suppliersModels.SupplierPayments.chave_acesso == nf.chave_acesso,
                        suppliersModels.SupplierPayments.parcela == parcela_int,
                    )
                    .first()
                )

                if exists:
                    updated = False
                    if exists.quantidade_parcelas != quantidade_parcelas:
                        exists.quantidade_parcelas = quantidade_parcelas
                        updated = True
                    if supplier and exists.supplier_id != supplier.id:
                        exists.supplier_id = supplier.id
                        updated = True
                    if updated:
                        db.add(exists)

                    skipped += 1
                    continue

                vencimento_dt = None
                if dup.dVenc:
                    try:
                        vencimento_dt = datetime.fromisoformat(dup.dVenc)
                    except ValueError:
                        vencimento_dt = None

                valor_float = None
                if dup.vDup is not None:
                    try:
                        valor_float = float(str(dup.vDup).replace(",", "."))
                    except ValueError:
                        valor_float = None

                new_entry = suppliersModels.SupplierPayments(
                    company_id=comp.id,
                    supplier_id=supplier.id,
                    chave_acesso=nf.chave_acesso,
                    parcela=parcela_int,
                    quantidade_parcelas=quantidade_parcelas,
                    valor=valor_float,
                    vencimento=vencimento_dt,
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


