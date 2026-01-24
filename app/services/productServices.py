from ..models import productModels
from ..schemas import productSchemas
from sqlalchemy.orm import Session
from ..database import get_db
from fastapi import Depends
from typing import Optional
from .userServices import User
import requests
from ..server_config import API_URL


products = {}

class Product:
    def __init__(
        self, 
        product: Optional[productModels.Product] = None,
        pid: Optional[int] = None,
        db: Session = Depends(get_db)
    ):
        self.db = db
        self.pid = pid or (product.id if product else None)
 
        self.company_id = None
        self.sku = None
        self.name = None
        self.picture = None
        self.last_entry_price = 0
        self.price_after_taxes = 0
        self.stock_unit_price = 0
        self.stock = 0
        self.virtual_stock = 0
        self.available_stock = 0
        self.created_by = None
        self.created_at = None
        self.updated_by = None
        self.updated_at = None

        self._load_product()

    def _load_product(self, refresh=False):
        if not self.pid:
            raise ValueError("Please inform product id (pid)")

        if self.pid in products and not refresh:
            cached = products[self.pid]
            # self.__dict__.update(cached.__dict__)
            # return
            return cached

        query = (
            self.db.query(productModels.Product)
            .filter(productModels.Product.id == self.pid)
            .first()
        )

        if query:
            for column in productModels.Product.__table__.columns:
                setattr(self, column.name, getattr(query, column.name))

            products[self.pid] = self

    def get_product(self, refresh=False, identifs=False):
        if not hasattr(self, "company_id") or self.company_id is None or refresh:
            self._load_product()

        return productSchemas.ProductResponse(
            id=self.pid,
            company_id=self.company_id,
            sku=self.sku,
            name=self.name,
            picture=self.picture,
            last_entry_price=self.last_entry_price,
            price_after_taxes=self.price_after_taxes,
            stock_unit_price=self.stock_unit_price,
            stock=self.stock,
            virtual_stock=self.virtual_stock,
            available_stock=self.available_stock,
            created_by=User(user_id=self.created_by, db=self.db).get_user(),
            created_at=self.created_at,
            updated_by=User(user_id=self.updated_by, db=self.db).get_user(),
            updated_at=self.updated_at,
            identificators=self.get_identificators() if identifs else None
        )
    
    def alter_field(self, **values):
        product = (
            self.db.query(productModels.Product)
            .filter(productModels.Product.id == self.pid)
        )
        product.update(values)
        aval_qt = product.first().available_stock if product.first().available_stock else 0
        vir_qt = product.first().virtual_stock if product.first().virtual_stock else 0
        
        product.first().stock = aval_qt + vir_qt
        print(product.first().stock)
        self.db.commit()

        # # manter o objeto em memória atualizado
        # for k, v in values.items():
        #     setattr(self, k, v)
        self._load_product(refresh=True)


    def get_identificators(self):
        query = self.db.query(productModels.ProductIdentificator).filter(productModels.ProductIdentificator.product_id == self.pid).all()
        return [productSchemas.IdentifResponse(
            product_id=item.product_id,
            code=item.code,
            code_type=item.code_type,
            created_at=item.created_at,
            created_by=User(user_id=item.created_by, db=self.db).get_user()
        ) for item in query]



    def _update_price(self):
        # req = requests.get(f"{API_URL}/invoices/product/{}")
        pass        

        




