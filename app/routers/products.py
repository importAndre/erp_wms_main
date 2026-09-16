from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from ..models import productModels, compositionModels, identificatorsModels, stockModels
from ..schemas import productSchemas
from ..database import get_db
from ..oauth2 import get_current_user
from ..services import userServices, productServices, compositionServices, finantialServices
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Union
import requests
from ..server_config import API_URL
from sqlalchemy import exists

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

    query = db.query(productModels.Product).filter(productModels.Product.company_id == product.company_id)\
            .filter(productModels.Product.sku == product.sku).first()
    if query:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="SKU already registered")
    
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

@router.get(
    "/", 
    response_model=Union[List[productSchemas.ProductResponse], Dict]
)
def get_products(
    current_user=Depends(get_current_user),
    refresh: Optional[bool] = False,
    stock_refresh: Optional[bool] = False,
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
            loaded_products.append(productServices.Product(product=item, db=db, load_stock=stock_refresh).get_product(refresh=refresh))
            PROCESSED += 1
        PROCESSING = False
        PROCESSED = 0
    return loaded_products

@router.get(
    "/pid/{pid}", 
    response_model=Union[productSchemas.ProductResponse, productSchemas.ProductAddressResponse]
)
def get_product(
    pid: int,
    address: Optional[bool] = False,
    date: Optional[datetime] = None,
    historical_prices: Optional[bool] = False,
    refresh: Optional[bool] = None,
    load_stock: Optional[bool] = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if refresh:
        # prod = productServices.Product(pid=pid, db=db, load_stock=load_stock)
        prod = productServices.Product(pid=pid, db=db, load_stock=True)
    else:
        prod = productServices.Product(pid=pid, db=db, load_stock=False)

    if historical_prices:
        prod.get_historical_price()

    if address:
        return prod.get_addresses()
    if date:
        return prod.get_product_date(date=date)
    

    return prod.get_product(refresh=refresh)

@router.put(
    "/edit", 
    response_model=productSchemas.ProductResponse
)
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



@router.get(
    "/search/{sku}"
)
def search_by_sku(
    sku: str,
    refresh: Optional[bool] = True,
    # current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    product_query = db.query(productModels.Product).filter(productModels.Product.sku == sku).first()
    if product_query:
        prod_obj = productServices.Product(product=product_query, db=db)
        # prod_obj._update_price()
        return prod_obj.get_product(refresh=refresh)
    composition_query = db.query(compositionModels.Composition).filter(compositionModels.Composition.sku == sku).first()
    if composition_query:
        comp_obj = compositionServices.Composition(cid=composition_query.id, db=db)
        # comp_obj.get_comp_entries()
        return comp_obj.get_composition(refresh=refresh)
    return {"message": f"Product {sku} not found"}



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


@router.get("/stock-date")
def get_product_date(
    pid: int,
    date: datetime,
    db: Session = Depends(get_db)
):
    prod = productServices.Product(pid=pid, db=db)
    # prod_response = prod.get_product()
    old_quantity = prod.get_product_date(date=date)
    # print(old_quantity)

    return old_quantity


@router.get("/virtual")
def update_virtual_stock(
    pid: int,
    date: Optional[datetime] = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)    
):
    from .mercado_livre import update_virtual_stock
    if not date:
        date = datetime.now()
    product = productServices.Product(pid=pid, db=db).get_product()
    comps = []

    def get_full_stock(sku: str, company_id: int) -> int:
        url = f"{API_URL}/mercado-livre/listings/full-stock"
        params = {
            "company_id": company_id,
            "sku": sku,
            "date": date
        }
        req = requests.get(url=url, params=params)
        if req.status_code == 200:
            data = req.json()
            print(data)
            try:
                return data[sku]['stock']
            except KeyError:
                return 0
        return 0


    pid_full_stock = 0
    compositions = db.query(compositionModels.CompositionItems).filter(compositionModels.CompositionItems.product_id == pid).all()
    for c in compositions:
        comp_obj = compositionServices.Composition(cid=c.composition_id, db=db).get_composition()
        full_stock = get_full_stock(sku=comp_obj.sku, company_id=comp_obj.company_id)
        for p in comp_obj.items:
            if p.product.id == pid:
                pid_full_stock += full_stock * p.amount_required
                # if full_stock > 0:
                #     print("comp", comp_obj.sku, 'stock', full_stock, "pid_full_stock", pid_full_stock)


    new_move = stockModels.VirtualStockMovements(
        product_id=product.id,
        quantity=pid_full_stock,
        location='ml_fulfillment',
        created_at=date
    )
    print(new_move.product_id, new_move.quantity)
    db.add(new_move)
    db.commit()
    db.refresh(new_move)
    return new_move


@router.get("/sales")
def product_sales(
    company_id: int,
    product_id: Optional[List[int]] = Query(default=None),
    date_begin: Optional[datetime] = None,
    date_end: Optional[datetime] = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from .finantials import get_dre
    products = []
    if product_id:
        for item in product_id:
            products.append(productServices.Product(pid=item, db=db))
    else:
        query = db.query(productModels.Product).filter(productModels.Product.company_id == company_id).all()
        for item in query:
            products.append(productServices.Product(pid=item.id, db=db))
    # dre = finantialServices.Dre(company_id=company_id, date_begin=date_begin, date_end=date_end, db=db).get_dre()
    dre = get_dre(
            company_id=company_id,
            date_begin=date_begin,
            date_end=date_end,
            current_user=current_user,
            db=db,
    )

    result = {}
    for p in products:
        if date_end:
            atual = p.get_product_date(date=date_end)
        else:
            atual = p.get_product()
        purchases = p.get_purchases(date_begin=date_begin, date_end=date_end)
        old = p.get_product_date(date=date_begin)
        sales = p.get_sales(date_begin=date_begin, date_end=date_end)
        # print(p.sku, len(sales.invoices))
        revenue_percentage = sales.v_prod / dre.faturamento
        result[atual.sku] = {
            "product": atual,
            "old_product": old,
            "sold_quantity": sales.quantity,
            "total_revenue": sales.v_prod,
            "bought_quantity": purchases.quantity,
            "bought_value": purchases.v_prod,
            "old_stock": old.stock_value,
            "old_stock_qt": old.stock,
            "current_stock": atual.stock_value,
            "current_stock_qt": atual.stock,
            "cmv": old.stock_value + purchases.v_prod - atual.stock_value,
            "revenue_percentage": revenue_percentage,
            "gross_profit": dre.lucro_bruto * revenue_percentage,
            "liquid_profit": dre.lucro_operacional * revenue_percentage
        }

    return result



@router.get("/mktplace-sales/{product_id}")
def get_mkt_place_sales(
    product_id: int,
    date_begin: Optional[datetime] = None,
    date_end: Optional[datetime] = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    prod_obj = productServices.Product(pid=product_id, db=db)
    prod = prod_obj.get_product()
    compositions_ids = db.query(compositionModels.CompositionItems).filter(compositionModels.CompositionItems.product_id == product_id).all()
    comps = db.query(compositionModels.Composition).filter(compositionModels.Composition.id.in_([c.composition_id for c in compositions_ids])).all()
    skus = [prod.sku]
    skus.append([comp.sku for comp in comps])
