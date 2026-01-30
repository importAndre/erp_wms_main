from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..models import suppliersModels
from ..schemas import supplierSchemas
from ..database import get_db
from ..oauth2 import get_current_user
from ..services import userServices, supplierServices
from datetime import datetime
from typing import List, Optional

router = APIRouter(
    prefix="/suppliers",
    tags=["suppliers"],
    responses={404: {"description": "Not found"}},
)

@router.post("/create", response_model=supplierSchemas.SupplierResponse)
def create_product(
    supplier: supplierSchemas.SupplierCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = userServices.User(user=current_user, db=db)
    user.check_users_permission(task='create_supplier')
    
    new_product = suppliersModels.Suppliers(
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

    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return new_product



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