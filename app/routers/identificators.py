from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..models import identificatorsModels
from ..schemas import identificatorsSchemas
from ..database import get_db
from ..oauth2 import get_current_user
from ..services import userServices, productServices, compositionServices
from datetime import datetime
from typing import List, Optional

router = APIRouter(
    prefix="/identificators",
    tags=["identificators"],
    responses={404: {"description": "Not found"}},
)


loaded_products = []

@router.post("/create", response_model=identificatorsSchemas.IdentifResponse)
def create_product(
    identificator: identificatorsSchemas.IdentifCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = userServices.User(user=current_user)
    
    new_identif = identificatorsModels.Identificators(
        identif_type=identificator.identif_type,
        company_id=identificator.company_id,
        is_composition=identificator.is_composition,
        product_id=identificator.product_id,
        composition_id=identificator.composition_id,
        value=identificator.value
    )   

    db.add(new_identif)
    db.commit()
    db.refresh(new_identif)

    return new_identif

@router.get("/get/{value}")
def get_identif(
    value: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(identificatorsModels.Identificators).filter(identificatorsModels.Identificators.value == value).first()
    if not query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Value {value} not found")
    if query.is_composition:
        return compositionServices.Composition(cid=query.composition_id, db=db).get_composition()
    else:
        return productServices.Product(pid=query.product_id, db=db).get_product()