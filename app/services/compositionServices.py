from ..models import compositionModels, identificatorsModels
from ..schemas import compositionSchemas, finantialsSchemas
from sqlalchemy.orm import Session
from ..database import get_db
from fastapi import Depends
from typing import Optional
from .productServices import Product
from .userServices import User
import requests
from ..server_config import API_URL

compositions = {}

class Composition:
    def __init__(
        self,
        cid: int,
        db: Session = Depends(get_db)
    ):
        self.cid = cid
        self.db = db
        self.company_id = None
        self.products = []
        self.identifs = None
        self.items = []
        self.last_entry_price = None
        self._load_composition()

    def _load_composition(self, refresh=True):
        comp = (
            self.db.query(compositionModels.Composition)
            .filter(compositionModels.Composition.id == self.cid)
            .first()
        )
        if not comp:
            return

        for column in compositionModels.Composition.__table__.columns:
            setattr(self, column.name, getattr(comp, column.name))

        items = (
            self.db.query(compositionModels.CompositionItems)
            .filter(compositionModels.CompositionItems.composition_id == self.cid)
            .all()
        )

        # limpa estado antes de recalcular
        self.products = []
        self.items = []
        self.identifs = None

        self.last_entry_price = 0
        self.price_after_taxes = 0
        self.stock_unit_price = 0
        self.stock = 0
        self.virtual_stock = 0
        self.available_stock = 0

        for i in items:
            self.company_id = i.company_id

            prod_obj = Product(pid=i.product_id, db=self.db)
            prod = prod_obj.get_product(refresh=refresh)

            item = compositionSchemas.ItemResponse(
                product=prod,
                amount_required=i.amount_required
            )

            self.items.append(prod_obj)
            self.products.append(item)

            self.last_entry_price += (item.product.last_entry_price or 0) * item.amount_required
            self.price_after_taxes += (item.product.price_after_taxes or 0) * item.amount_required
            self.stock_unit_price += (item.product.stock_unit_price or 0) * item.amount_required

        stocks = []
        virtuals = []
        availables = []

        for p in self.products:
            stocks.append((p.product.stock or 0) / p.amount_required)
            virtuals.append((p.product.virtual_stock or 0) / p.amount_required)
            availables.append((p.product.available_stock or 0) / p.amount_required)

        self.stock = min(stocks) if stocks else 0
        self.virtual_stock = min(virtuals) if virtuals else 0
        self.available_stock = min(availables) if availables else 0

        comp.last_entry_price = self.last_entry_price
        comp.price_after_taxes = self.price_after_taxes
        comp.stock_unit_price = self.stock_unit_price
        comp.stock = self.stock
        comp.virtual_stock = self.virtual_stock
        comp.available_stock = self.available_stock

        self.db.commit()
        self.db.refresh(comp)

        self.get_comp_entries()

        compositions[self.cid] = self

    
    def get_composition(self, refresh=False):
        if self.last_entry_price is None or refresh:
            self._load_composition(refresh=refresh)
        # print("sku", self.sku, "created_by", self.created_by, "updated_by", self.updated_by)
        return compositionSchemas.CompositionResponse(
            id=self.cid,
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
            items=self.products,
            identificators=self.identifs
        )
    
    def get_identifs(self):
        query = self.db.query(identificatorsModels.Identificators).filter(identificatorsModels.Identificators.composition_id == self.cid).all()
        self.identifs = [compositionSchemas.IdentifResponse(
            composition_id=item.composition_id,
            code=item.value,
            code_type=item.identif_type,
            id=item.id
            # created_at=item.created_at,
            # created_by=User(user_id=item.created_by, db=self.db).get_user()
        ) for item in query]
        return self.identifs


    def get_comp_entries(self):
        if not self.identifs:
            self.get_identifs()
        dh_emit = None
        for i in self.identifs:
            if i.code_type == 'supplier_code':
                params = {"cprod": {i.code}}
                req = requests.get(f"{API_URL}/invoices/product", params=params)
                if req.status_code == 200:
                    data = req.json()

                    invoice = finantialsSchemas.InvoiceBase.model_validate(data['invoice'])
                    item_inv = finantialsSchemas.InvoiceItemBase.model_validate(data['item'])
                    taxes = finantialsSchemas.TaxesBase.model_validate(data)

                    price = item_inv.v_un_com / self.products[0].amount_required
                    if not dh_emit:
                        dh_emit = invoice.dh_emissao

                    new_dh_emit  = invoice.dh_emissao
                    if new_dh_emit >= dh_emit:
                        for item in taxes.taxes:
                            if item.item_id != item_inv.id:
                                continue
                            if item.tax == 'ICMS':
                                icms = price * (item.p_aliq / 100)
                                # print("v_icms", self.v_icms)
                            
                            elif item.tax == 'IPI':
                                ipi = price * (item.p_aliq / 100)
                            st = 0

                    item_prod = self.items[0]
                    item_prod.calculate_price(
                        price=price,
                        icms=icms,
                        ipi=ipi,
                        st=st
                        )


        
