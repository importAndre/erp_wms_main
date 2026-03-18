from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..models import productModels, compositionModels, identificatorsModels
from ..schemas import productSchemas
from ..database import get_db
from ..oauth2 import get_current_user
from ..services import userServices, productServices, compositionServices
from datetime import datetime
from typing import List, Optional, Dict, Union

router = APIRouter(
    prefix="/products",
    tags=["products"],
    responses={404: {"description": "Not found"}},
)


loaded_products = []

@router.post("/create", response_model=productSchemas.ProductResponse)
def create_product(
    product: productSchemas.ProductCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = userServices.User(user=current_user, db=db)
    user.check_users_permission(task='create_product')
    
    new_product = productModels.Product(
        company_id=product.company_id,
        sku=product.sku,
        name=product.name,
        picture=product.picture,
        supplier_id=product.supplier_id,
        created_by=user.id,
        updated_by=user.id,
        updated_at=datetime.now(),
        created_at=datetime.now()
    )   

    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    prod = productServices.Product(product=new_product, db=db).get_product()
    loaded_products.append(prod)
    return prod


PROCESSING = False
PROCESSED = 0

@router.get("/", response_model=Union[List[productSchemas.ProductResponse], Dict])
def get_products(
    current_user=Depends(get_current_user),
    refresh: Optional[bool] = False,
    db: Session = Depends(get_db)
):
    global loaded_products
    global PROCESSING, PROCESSED
    if not loaded_products or refresh:
        query = db.query(productModels.Product).all()
        total = len(query)
        loaded_products = []
        if PROCESSING:
            return {
                "message": f"Please await",
                "values": {
                    "processed": PROCESSED,
                    "total": total,
                    "percentage": (PROCESSED / total) * 100
                }
                }
        for item in query:
            PROCESSING = True
            loaded_products.append(productServices.Product(product=item, db=db).get_product(refresh=refresh))
            PROCESSED += 1
        PROCESSING = False
        PROCESSED = 0
    return loaded_products



@router.get("/pid/{pid}", response_model=productSchemas.ProductResponse)
def get_product(
    pid: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    prod = productServices.Product(pid=pid, db=db)
    return prod.get_product(refresh=True)

@router.put("/edit", response_model=productSchemas.ProductResponse)
def edit_product(
    product: productSchemas.ProductEdit,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not product.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="product.id is required")
    
    userServices.User(user=current_user, db=db).check_users_permission(task='edit_product')

    db_product = db.query(productModels.Product).filter(productModels.Product.id == product.id).first()

    for var, value in vars(product).items():
        if value is not None:
            setattr(db_product, var, value)

    db_product.updated_at = datetime.now()
    db_product.updated_by = current_user.id
    db.commit()
    db.refresh(db_product)

    return productServices.Product(product=db_product, db=db).get_product()



@router.get("/search/{sku}")
def search_by_sku(
    sku: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    product_query = db.query(productModels.Product).filter(productModels.Product.sku == sku).first()
    if product_query:
        prod_obj = productServices.Product(product=product_query, db=db)
        # prod_obj._update_price()
        return prod_obj.get_product(refresh=True)
    composition_query = db.query(compositionModels.Composition).filter(compositionModels.Composition.sku == sku).first()
    if composition_query:
        comp_obj = compositionServices.Composition(cid=composition_query.id, db=db)
        # comp_obj.get_comp_entries()
        return comp_obj.get_composition(refresh=True)
    return {"message": f"Product {sku} not found"}



from sqlalchemy import exists

@router.get("/not-identif")
def get_not_identifs(
    company_id: Optional[int] = 1,
    db: Session = Depends(get_db)
):
    products = db.query(productModels.Product).filter(
        productModels.Product.company_id == company_id,
        ~exists().where(
            identificatorsModels.Identificators.product_id == productModels.Product.id
        ).where(
            identificatorsModels.Identificators.identif_type == 'supplier_code'
        )
    ).all()

    return {
        "total": len(products),
        "products": products
    }
