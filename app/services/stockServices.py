from ..models import stockModels
from ..schemas import stockSchemas
from sqlalchemy.orm import Session
from ..database import get_db
from typing import Optional
from fastapi import Depends, HTTPException, status
from datetime import datetime

class Address:
    def __init__(
        self,
        address: Optional[stockModels.Address] = None,
        add_id: Optional[int] = None,
        db: Session = Depends(get_db)
    ):
        self.address = address
        self.add_id = add_id if add_id else None
        self.warehouse = None
        self.block = None
        self.street = None
        self.column = None
        self.floor = None
        self.full_address = None
        self.address_type = None
        self.weight_supported = None
        self.weight = None
        self.height = None
        self.width = None
        self.depth = None
        self.db = db

        self._load_address()

    def _load_address(self):
        if self.address:
            return
        if not self.add_id:
            raise AttributeError("Addres id required")
        
        query = self.db.query(stockModels.Address)\
                .filter(stockModels.Address.id == self.add_id).first()
        if not query:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Address not found')
        
        self.address = query
        self.warehouse = query.warehouse
        self.block = query.block
        self.street = query.street
        self.column = query.column
        self.floor = query.floor
        self.full_address = query.full_address
        self.address_type = query.address_type
        self.weight_supported = query.weight_supported
        self.weight = query.weight
        self.height = query.height
        self.width = query.width
        self.depth = query.depth
        self.add_id = query.id

    def get_address(self, refresh=False):
        if not hasattr(self, "warehouse") or self.warehouse is None or refresh:
            self._load_address
        return stockSchemas.AddressResponse(
            warehouse=self.warehouse,
            block=self.block,
            street=self.street,
            column=self.column,
            floor=self.floor,
            address_type=self.address_type,
            weight_supported=self.weight_supported,
            weight=self.weight,
            height=self.height,
            width=self.width,
            depth=self.depth,
            id=self.add_id,
            full_address=self.full_address
        )
    
    def get_products(self):
        from .productServices import Product
        if not self.warehouse:
            self._load_address()

        query = self.db.query(stockModels.AddressProducts)\
            .filter(stockModels.AddressProducts.address_id == self.add_id).all()

        products = []
        for item in query:
            product = Product(pid=item.product_id, db=self.db).get_product()
            add_prod = stockSchemas.AddressItemResponse(
                product=product,
                quantity=item.quantity
            )
            products.append(add_prod)

        return products
    
    def stock_move(self, movement: stockSchemas.StockMovementCreate):
        query = self.db.query(stockModels.AddressProducts)\
            .filter(stockModels.AddressProducts.address_id == movement.address_id)\
            .filter(stockModels.AddressProducts.product_id == movement.product_id).first()

        if query:
            if movement.method:
                query.quantity += movement.quantity
            else:
                query.quantity -= movement.quantity
            
            self.db.commit()

        else:
            new_product = stockModels.AddressProducts(
                address_id=movement.address_id,
                product_id=movement.product_id,
                quantity=movement.quantity,
                updated_at=datetime.now()
            )
            self.db.add(new_product)
            self.db.commit()
            self.db.refresh(new_product)


            