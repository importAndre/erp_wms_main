from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..models import identificatorsModels
from ..schemas import identificatorsSchemas
from ..database import get_db
from ..oauth2 import get_current_user
from ..services import userServices, productServices, compositionServices
from datetime import datetime
from typing import List, Optional
from sqlalchemy.exc import IntegrityError

router = APIRouter(
    prefix="/identificators",
    tags=["identificators"],
    responses={404: {"description": "Not found"}},
)


identifis_types = [
    'supplier_code',
    'ean_trib'
    'ean'
    'dum',
    'ncm',
    'cfop',
    'orig'
]


loaded_products = []

@router.post("/create", response_model=identificatorsSchemas.IdentifResponse)
def create_identifs(
    identificator: identificatorsSchemas.IdentifCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = userServices.User(user=current_user, db=db)
    
    new_identif = identificatorsModels.Identificators(
        identif_type=identificator.identif_type,
        company_id=identificator.company_id,
        is_composition=identificator.is_composition,
        product_id=identificator.product_id,
        composition_id=identificator.composition_id,
        value=identificator.value
    )   
    print(new_identif)

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
    

@router.put("/update/{identif_id}", response_model=identificatorsSchemas.IdentifResponse)
def update_identif(
    identif_id: int,
    identificator: identificatorsSchemas.IdentifCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = userServices.User(user=current_user, db=db)

    query = db.query(identificatorsModels.Identificators).filter(
        identificatorsModels.Identificators.id == identif_id
    ).first()

    if not query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Identificator {identif_id} not found"
        )

    # Validação de consistência
    # if identificator.is_composition:
    #     if not identificator.composition_id:
    #         raise HTTPException(
    #             status_code=status.HTTP_400_BAD_REQUEST,
    #             detail="For composition identificator, composition_id is required"
    #         )
    #     if identificator.product_id is not None:
    #         raise HTTPException(
    #             status_code=status.HTTP_400_BAD_REQUEST,
    #             detail="For composition identificator, product_id must be null"
    #         )
    # else:
    #     if not identificator.product_id:
    #         raise HTTPException(
    #             status_code=status.HTTP_400_BAD_REQUEST,
    #             detail="For product identificator, product_id is required"
    #         )
    #     if identificator.composition_id is not None:
    #         raise HTTPException(
    #             status_code=status.HTTP_400_BAD_REQUEST,
    #             detail="For product identificator, composition_id must be null"
    #         )

    query.identif_type = identificator.identif_type if identificator.identif_type else query.identif_type
    query.company_id = identificator.company_id if identificator.company_id else query.company_id
    query.is_composition = identificator.is_composition if identificator.is_composition else query.is_composition
    query.product_id = identificator.product_id if identificator.product_id else query.product_id
    query.composition_id = identificator.composition_id if identificator.composition_id else query.composition_id
    query.value = identificator.value if identificator.value else query.value

    # try:
    db.commit()
    db.refresh(query)
    # except IntegrityError:
    #     db.rollback()
    #     raise HTTPException(
    #         status_code=status.HTTP_409_CONFLICT,
    #         detail="Already exists an identificator with this company_id, identif_type and value"
    #     )

    return query