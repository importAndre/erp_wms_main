from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..models import compositionModels
from ..schemas import compositionSchemas
from ..database import get_db
from ..oauth2 import get_current_user
from ..services import compositionServices
from datetime import datetime
from typing import List, Optional
from sqlalchemy.exc import IntegrityError
from ..services.userServices import User



router = APIRouter(
    prefix="/compositions",
    tags=["compositions"],
    responses={404: {"description": "Not found"}},
)

loaded_compositions = []

@router.post("/create")
def create_composition(
    composition: compositionSchemas.CompositionCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    existing = db.query(compositionModels.Composition).filter(compositionModels.Composition.sku == composition.sku).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="SKU already registered")

    new_comp = compositionModels.Composition(
        company_id=composition.company_id,
        sku=composition.sku,
        name=composition.name,
        picture=composition.picture,
        created_at=datetime.now(),
        created_by=current_user.id,
        updated_at=datetime.now(),
        updated_by=current_user.id
    )

    db.add(new_comp)
    db.commit()
    db.refresh(new_comp)

    return new_comp


@router.post("/add-item")
def add_item(
    items: compositionSchemas.AddCompositionItem,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    
    comp = db.query(compositionModels.Composition).filter(compositionModels.Composition.id == items.composition_id).first()
    if not comp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    for i in items.items:
        try:
            new_item = compositionModels.CompositionItems(
                company_id=comp.company_id,
                composition_id=items.composition_id,
                product_id=i.product_id,
                amount_required=i.amount_required
            )
            db.add(new_item)
            db.commit()
            db.refresh(new_item)
        except IntegrityError as e:
            db.rollback()
            if "uq_composition_product" in str(e.orig):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Item {i.product_id} already in composition"
                )

    return compositionServices.Composition(cid=comp.id, db=db).get_composition()


@router.get("/")
def get_compositions(
    current_user=Depends(get_current_user),
    refresh: Optional[bool] = False,
    db: Session = Depends(get_db)
):

    global loaded_compositions
    if not loaded_compositions or refresh:
        query = db.query(compositionModels.Composition).all()
        for comp in query:
            comp_obj = compositionServices.Composition(cid=comp.id, db=db).get_composition()
            loaded_compositions.append(comp_obj)
    return loaded_compositions
    
    
        