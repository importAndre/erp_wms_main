from ..models import compositionModels
from ..schemas import compositionSchemas
from sqlalchemy.orm import Session
from ..database import get_db
from fastapi import Depends
from typing import Optional
from .productServices import Product
from .userServices import User

compositions = {}

class Composition:
    def __init__(
        self,
        cid: int,
        db: Session = Depends(get_db)
    ):
        self.cid = cid
        self.db = db
        self.products = []
        self._load_composition()

    def _load_composition(self):
        if self.cid in compositions:
            cached = compositions[self.cid]
            self.__dict__.update(cached.__dict__)

        comp = self.db.query(compositionModels.Composition).filter(compositionModels.Composition.id == self.cid).first()
        if comp:
            for column in compositionModels.Composition.__table__.columns:
                if column.name in ['updated_by', 'created_by']:
                    setattr
                setattr(self, column.name, getattr(comp, column.name))

        items = self.db.query(compositionModels.CompositionItems).filter(compositionModels.CompositionItems.composition_id == self.cid).all()
        for i in items:
            prod = Product(pid=i.product_id, db=self.db).get_product()
            amount = i.amount_required
            self.products.append(compositionSchemas.ItemResponse(
                product=prod,
                amount_required=amount
            ))
        
        compositions[self.cid] = self

    
    def get_composition(self, refresh=False):
        if not self.company_id and refresh:
            self._load_composition()
        return compositionSchemas.CompositionResponse(
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
            updated_by=User(user_id=self.updated_by, db=self.db).get_user(),
            updated_at=self.updated_at,
            created_at=self.created_at,
            items=self.products
        )