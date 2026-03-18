from datetime import datetime
from ..models import productModels, identificatorsModels
from ..schemas import productSchemas, finantialsSchemas
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
        self.identifs = None
        self.supplier = None

        self._load_product()

    def _load_product(self, refresh=False):
        if not self.pid:
            raise ValueError("Please inform product id (pid)")

        if not refresh and self._product:
            if not self.supplier:
                self._load_supplier()
            return

        query = (
            self.db.query(productModels.Product)
            .filter(productModels.Product.id == self.pid)
            .first()
        )

        if query:
            for column in productModels.Product.__table__.columns:
                setattr(self, column.name, getattr(query, column.name))
            self._load_supplier()
            self._update_price()


    def get_product(self, refresh=False):
        if not hasattr(self, "company_id") or self.company_id is None or refresh:
            self._load_product(refresh=refresh)

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
            identificators=self.identifs,
            supplier=self.supplier
        )

        return data
    

    def _load_supplier(self):
        if not self.supplier_id:
            return None
        if not self.supplier:
            self.supplier = Supplier(sid=self.supplier_id, db=self.db).get_supplier()
        return self.supplier

    
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
        self.db.commit()

        # # manter o objeto em memória atualizado
        # for k, v in values.items():
        #     setattr(self, k, v)
        # self._load_product(refresh=True)


    def get_identificators(self):
        query = self.db.query(identificatorsModels.Identificators).filter(identificatorsModels.Identificators.product_id == self.pid).all()
        self.identifs = [productSchemas.IdentifResponse(
            product_id=item.product_id,
            code=item.value,
            code_type=item.identif_type,
            id=item.id
            # created_at=item.created_at,
            # created_by=User(user_id=item.created_by, db=self.db).get_user()
        ) for item in query]
        return self.identifs



    def _update_price(self):
        if not self.identifs:
            self.get_identificators()
        dh_emit = None
        for i in self.identifs:
            if i.code_type == 'supplier_code':
                params = {"cprod": {i.code}, "supplier_cnpj": self.supplier.cnpj}
                req = requests.get(f"{API_URL}/invoices/product", params=params)
                if req.status_code == 200:
                    data = req.json()
                    # print(data)
                    if not data:
                        print(f"not data for {self.sku}")
                        return

                    invoice = finantialsSchemas.InvoiceBase.model_validate(data['invoice'])
                    item_inv = finantialsSchemas.InvoiceItemBase.model_validate(data['item'])
                    taxes = finantialsSchemas.TaxesBase.model_validate(data)
                    # events = finantialsSchemas.EventsBase.model_validate(data['events'])
                    if not dh_emit:
                        dh_emit = invoice.dh_emissao

                    self.p_icms = 0
                    self.v_icms = 0
                    self.p_ipi = 0
                    self.v_ipi = 0

                    self.add_identif(ean=item_inv.ean, ean_trib=item_inv.ean_trib, ncm=item_inv.ncm, cfop=item_inv.cfop)

                    new_dh_emit = invoice.dh_emissao
                    if new_dh_emit >= dh_emit:
                        for item in taxes.taxes:
                            if item.item_id != item_inv.id:
                                continue
                            if item.tax == 'ICMS':
                                self.p_icms = item.p_aliq
                                if not item.p_aliq:
                                    self.p_icms = 0
                                self.v_icms = item_inv.v_un_com * (self.p_icms / 100)
                                self.add_identif(orig=item.orig)
                                # print("v_icms", self.v_icms)
                            
                            elif item.tax == 'IPI':
                                self.p_ipi = item.p_aliq
                                # print("p_pis", self.p_pis)
                                self.v_ipi = item_inv.v_un_com * (item.p_aliq / 100)
                                # print("v_pis", self.v_pis)

                            cofins = item_inv.v_un_com * 7.6 / 100
                            pis = item_inv.v_un_com * 1.65 / 100
                            st = 0

                            custo = item_inv.v_un_com - self.v_icms - pis - cofins + self.v_ipi + st


                        self.alter_field(last_entry_price=item_inv.v_un_com)
                        self.alter_field(price_after_taxes=custo)

    def calculate_price(self, price, icms, ipi, st):
        cofins = price * 7.6 / 100
        pis = price * 1.65 / 100
        cost = price - icms - pis - cofins + ipi + st
        self.alter_field(last_entry_price=price)
        self.alter_field(price_after_taxes=cost)

    def add_identif(
        self, 
        ean: Optional[str] = None, 
        ean_trib: Optional[str] = None, 
        ncm: Optional[str] = None, 
        cfop: Optional[str] = None, 
        orig: Optional[str] = None
    ):
        if ean:
            query = self.db.query(identificatorsModels.Identificators)\
                .filter(identificatorsModels.Identificators.product_id == self.pid)\
                .filter(identificatorsModels.Identificators.value == ean).first()
            if not query:
                new_identif = identificatorsModels.Identificators(
                    identif_type='ean',
                    company_id=self.company_id,
                    is_composition=False,
                    product_id=self.pid,
                    value=ean
                )
                self.db.add(new_identif)
                self.db.commit()
                self.db.refresh(new_identif)
        if ean_trib:
            query = self.db.query(identificatorsModels.Identificators)\
                .filter(identificatorsModels.Identificators.product_id == self.pid)\
                .filter(identificatorsModels.Identificators.value == ean_trib).first()
            if not query:
                new_identif = identificatorsModels.Identificators(
                    identif_type='ean_trib',
                    company_id=self.company_id,
                    is_composition=False,
                    product_id=self.pid,
                    value=ean_trib
                )
                self.db.add(new_identif)
                self.db.commit()
                self.db.refresh(new_identif)
        if ncm:
            query = self.db.query(identificatorsModels.Identificators)\
                .filter(identificatorsModels.Identificators.product_id == self.pid)\
                .filter(identificatorsModels.Identificators.value == ncm).first()
            if not query:
                new_identif = identificatorsModels.Identificators(
                    identif_type='ncm',
                    company_id=self.company_id,
                    is_composition=False,
                    product_id=self.pid,
                    value=ncm
                )
                self.db.add(new_identif)
                self.db.commit()
                self.db.refresh(new_identif)
        if cfop:
            query = self.db.query(identificatorsModels.Identificators)\
                .filter(identificatorsModels.Identificators.product_id == self.pid)\
                .filter(identificatorsModels.Identificators.value == cfop).first()
            if not query:
                new_identif = identificatorsModels.Identificators(
                    identif_type='cfop',
                    company_id=self.company_id,
                    is_composition=False,
                    product_id=self.pid,
                    value=cfop
                )
                self.db.add(new_identif)
                self.db.commit()
                self.db.refresh(new_identif)
        if orig:
            query = self.db.query(identificatorsModels.Identificators)\
                .filter(identificatorsModels.Identificators.product_id == self.pid)\
                .filter(identificatorsModels.Identificators.value == orig).first()
            if not query:
                new_identif = identificatorsModels.Identificators(
                    identif_type='orig',
                    company_id=self.company_id,
                    is_composition=False,
                    product_id=self.pid,
                    value=orig
                )
                self.db.add(new_identif)
                self.db.commit()
                self.db.refresh(new_identif)
                




