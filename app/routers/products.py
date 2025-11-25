from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..models import productModels
from ..schemas import productSchemas
from ..database import get_db
from ..oauth2 import get_current_user
from ..services import userServices, productServices
from datetime import datetime
from typing import List, Optional

router = APIRouter(
    prefix="/products",
    tags=["products"],
    responses={404: {"description": "Not found"}},
)


loaded_products = []

@router.post("/create", response_model=productSchemas.ProductCreate)
def create_product(
    product: productSchemas.ProductCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = userServices.User(user=current_user)
    
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

@router.get("/", response_model=List[productSchemas.ProductResponse])
def get_products(
    current_user=Depends(get_current_user),
    refresh: Optional[bool] = False,
    db: Session = Depends(get_db)
):
    global loaded_products
    if not loaded_products or refresh:
        query = db.query(productModels.Product).all()
        for item in query:
            loaded_products.append(productServices.Product(product=item, db=db).get_product())
    return loaded_products



@router.get("/pid/{pid}", response_model=productSchemas.ProductResponse)
def get_product(
    pid: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    prod = productServices.Product(pid=pid, db=db)
    return prod.get_product()

@router.put("/edit", response_model=productSchemas.ProductResponse)
def edit_product(
    product: productSchemas.ProductEdit,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not product.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="product.id is required")

    db_product = db.query(productModels.Product).filter(productModels.Product.id == product.id).first()

    for var, value in vars(product).items():
        if value is not None:
            setattr(db_product, var, value)

    db_product.updated_at = datetime.now()
    db_product.updated_by = current_user.id
    db.commit()
    db.refresh(db_product)

    return productServices.Product(product=db_product, db=db).get_product()