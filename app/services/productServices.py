from ..models import productModels
from ..schemas import productSchemas
from sqlalchemy.orm import Session
from ..database import get_db
from fastapi import Depends
from typing import Optional
from .userServices import User
import requests
from ..server_config import API_URL
from .supplierServices import Supplier


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
        self._product = product
        self.company_id = product.company_id if product else None
        self.supplier_id = product.supplier_id if product else None
        self.sku = product.sku if product else None
        self.name = product.name if product else None
        self.picture = product.picture if product else None
        self.last_entry_price = product.last_entry_price if product else 0
        self.price_after_taxes = product.price_after_taxes if product else 0
        self.stock_unit_price = product.stock_unit_price if product else 0
        self.stock = product.stock if product else 0
        self.virtual_stock = product.virtual_stock if product else 0
        self.available_stock = product.available_stock if product else 0
        self.created_by = product.created_by if product else None
        self.created_at = product.created_at if product else None
        self.updated_by = product.updated_by if product else None
        self.updated_at = product.updated_at if product else None

        self._load_product()

    def _load_product(self, refresh=False):
        if not self.pid:
            raise ValueError("Please inform product id (pid)")

        if not refresh and self._product:
            return

        query = (
            self.db.query(productModels.Product)
            .filter(productModels.Product.id == self.pid)
            .first()
        )

        if query:
            for column in productModels.Product.__table__.columns:
                setattr(self, column.name, getattr(query, column.name))


    def get_product(self, refresh=False, identifs=False):
        if not hasattr(self, "company_id") or self.company_id is None or refresh:
            self._load_product()

        data = productSchemas.ProductResponse(
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
            identificators=self.get_identificators() if identifs else None,
            supplier=self._load_supplier()
        )

        return data
    

    def _load_supplier(self):
        if not self.supplier_id:
            return None
        return Supplier(sid=self.supplier_id, db=self.db).get_supplier()

    
    def alter_field(self, **values):
        product = (
            self.db.query(productModels.Product)
            .filter(productModels.Product.id == self.pid)
        )
        product.update(values)
        product = product.first()
        aval_qt = product.available_stock if product.available_stock else 0
        vir_qt = product.virtual_stock if product.virtual_stock else 0
        
        product.stock = aval_qt + vir_qt
        print(product.stock)
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

        




