from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..models import productModels
from ..schemas import productSchemas
from ..database import get_db
from ..oauth2 import get_current_user
from ..services import userServices
from datetime import datetime

router = APIRouter(
    prefix="/products",
    tags=["products"],
    responses={404: {"description": "Not found"}},
)


@router.post("/create", response_model=productSchemas.ProductCreate)
def create_product(
    product: productSchemas.ProductCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = userServices.User(user=current_user)
    print(user.username)
    
    new_product = productModels.Product(
        company_id=product.company_id,
        sku=product.sku,
        name=product.name,
        picture=product.picture,
        created_by=user.id,
        updated_by=user.id,
        updated_at=datetime.now(),
        created_at=datetime.now()
    )

    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return new_product

