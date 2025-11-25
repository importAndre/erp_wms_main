from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..models import stockModels
from ..schemas import stockSchemas
from ..services.stockServices import Address
from ..database import get_db
from ..oauth2 import get_current_user
from ..services import userServices, productServices, stockServices
from datetime import datetime
from typing import List, Optional

router = APIRouter(
    prefix="/stock",
    tags=["stock"],
    responses={404: {"description": "Not found"}},
)


@router.get("/addresses")
def get_addresses(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(stockModels.Address).all()

@router.post("/create/address")
def create_address(
    add: stockSchemas.AddressCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    
    full_address = f'{add.warehouse}-{add.block}-{add.street}-{add.column}-{add.floor}'
    db_add = stockModels.Address(
        warehouse=add.warehouse,
        block=add.block,
        street=add.street,
        column=add.column,
        floor=add.floor,
        full_address=full_address,
        address_type=add.address_type,
        weight_supported=add.weight_supported,
        weight=add.weight,
        height=add.height,
        width=add.width,
        depth=add.depth
    )
    db.add(db_add)
    db.commit()
    db.refresh(db_add)

    return db_add


@router.post("/movement")
def create_stock_movement(
    movement: stockSchemas.StockMovementCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_move = stockModels.StockMovement(
        address_id=movement.address_id,
        method=movement.method,
        quantity=movement.quantity,
        motive=movement.motive,
        motive_link=movement.motive_link,
        created_by=current_user.id,
        created_at=datetime.now(),
    )
    db.add(new_move)
    db.commit()
    db.refresh(new_move)

    address = Address(add_id=movement.address_id, db=db)
    address.stock_move(movement=movement)

    product = productServices.Product(pid=movement.product_id, db=db)
    aval_qt = product.available_stock
    if not aval_qt:
        aval_qt = 0

    if not movement.method:
        alter_qt = aval_qt - movement.quantity
    else:
        alter_qt = aval_qt + movement.quantity

    product.alter_field(available_stock=alter_qt)

    return address.get_products()


@router.get("/address")
def get_address(
    address_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    add = stockServices.Address(add_id=address_id, db=db)
    return stockSchemas.AddressProductsResponse(
        address=add.get_address(),
        products=add.get_products()
        )