from datetime import datetime
from ..models import productModels, identificatorsModels, stockModels
from ..schemas import productSchemas, finantialsSchemas, stockSchemas, companySchemas
from sqlalchemy.orm import Session
from ..database import get_db
from fastapi import Depends
from typing import Optional
from .userServices import User
import requests
from ..server_config import API_URL
from .supplierServices import Supplier
from .companyServices import Company


products_cache = {}
products_date_cache = {}


def _date_cache_key(pid: int, date: datetime):
    if isinstance(date, datetime):
        date_key = date.isoformat()
    else:
        date_key = str(date)
    return (pid, date_key)


def _invalidate_product_date_cache(pid: int):
    for key in list(products_date_cache.keys()):
        if key[0] == pid:
            products_date_cache.pop(key, None)

class Product:
    def __init__(
        self, 
        product: Optional[productModels.Product] = None,
        pid: Optional[int] = None,
        # sku: Optional[str] = None,
        load_stock: Optional[bool] = False,
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
        self.last_entry = None
        self.last_sell = None
        self.addresses = productSchemas.ProductAddressResponse()
        self.company = None
        self.load_stock = load_stock
        # if sku:
        #     self.sku = sku

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

        # if not self.pid and self.sku:
        #     query = (  
        #         self.db.query(productModels.Product)
        #         .filter(productModels.Product.sku == self.sku)
        #         .first()
        #     )


        if query:
            for column in productModels.Product.__table__.columns:
                setattr(self, column.name, getattr(query, column.name))
            self._load_supplier()
            self.company = Company(company_id=self.company_id, db=self.db).get_company()
            if refresh:
                self._update_price()
                self._get_last_sell_date()
            if self.load_stock:
                self._update_stock(update_all=True)
            else:
                self._update_stock(update_all=False)


    def get_product(self, refresh=False):
        if not refresh and self.pid in products_cache:
            return products_cache[self.pid]
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
            last_entry=self.last_entry,
            last_sell=self.last_sell,
            stock_value=(self.stock or 0) * (self.last_entry_price or 0),
            created_by=User(user_id=self.created_by, db=self.db).get_user(),
            created_at=self.created_at,
            updated_by=User(user_id=self.updated_by, db=self.db).get_user(),
            updated_at=self.updated_at,
            identificators=self.identifs,
            supplier=self.supplier,
        )
        products_cache[self.pid] = data
        return data
    
    def invalidade_product_cache(self):
        products_cache.pop(self.pid, None)
        _invalidate_product_date_cache(self.pid)

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
        # print(product.stock)
        aval_qt = product.available_stock if product.available_stock else 0
        vir_qt = product.virtual_stock if product.virtual_stock else 0
        
        product.stock = aval_qt + vir_qt
        # print(product.stock)
        self.db.commit()
        self.invalidade_product_cache()

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

    def _update_stock(self, update_all=False):
        from ..routers.mercado_livre import update_virtual_stock
        from ..models import compositionModels
        from ..services import compositionServices
        def get_full_stock(sku: str, company_id: int) -> int:
            url = f"{API_URL}/mercado-livre/listings/full-stock"
            params = {
                "company_id": company_id,
                "sku": sku
            }
            req = requests.get(url=url, params=params)
            # print(req)
            if req.status_code == 200:
                data = req.json()
                try:
                    return data[sku]['stock']
                except KeyError:
                    return 0
            return 0

        def update_virtual():
            pid_full_stock = 0
            compositions = self.db.query(compositionModels.CompositionItems).filter(compositionModels.CompositionItems.product_id == self.pid).all()
            for c in compositions:
                comp_obj = compositionServices.Composition(cid=c.composition_id, db=self.db).get_composition()
                full_stock = get_full_stock(sku=comp_obj.sku, company_id=comp_obj.company_id)
                for p in comp_obj.items:
                    if p.product.id == self.pid:
                        pid_full_stock += full_stock * p.amount_required


            new_move = stockModels.VirtualStockMovements(
                product_id=self.id,
                quantity=pid_full_stock,
                location='ml_fulfillment',
                created_at=datetime.now()
            )
            self.db.add(new_move)
            self.db.commit()
            self.db.refresh(new_move)

            full = self.db.query(stockModels.VirtualStockMovements)\
                .filter(stockModels.VirtualStockMovements.product_id == self.pid)\
                .filter(stockModels.VirtualStockMovements.location == 'ml_fulfillment')\
                .order_by(stockModels.VirtualStockMovements.created_at.desc()).first()
            
            if full:
                self.alter_field(virtual_stock=full.quantity)
            else:
                self.alter_field(virtual_stock=0)

        def update_available():
            query = self.db.query(stockModels.StockMovement).filter(stockModels.StockMovement.product_id == self.pid).all()
            # print(len(query))
            stock = 0
            for item in query:
                if item.method:
                    stock += item.quantity
                else:
                    stock -= item.quantity
                # print(item.method, item.quantity, item.created_at, stock)
            return stock

        aval = update_available()
        self.alter_field(available_stock=aval)

        if update_all:
            update_virtual()

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
                        self.last_entry = new_dh_emit
                        for item in taxes.taxes:
                            if item.item_id != item_inv.id:
                                continue
                            if item.tax == 'ICMS':
                                self.p_icms = item.p_aliq
                                if not item.p_aliq:
                                    self.p_icms = 0
                                self.v_icms = item_inv.v_un_com * (self.p_icms / 100)
                                self.add_identif(orig=item.orig)
                            
                            elif item.tax == 'IPI':
                                self.p_ipi = item.p_aliq
                                self.v_ipi = item_inv.v_un_com * (item.p_aliq / 100)

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


    def get_product_date(self, date: datetime):
        cache_key = _date_cache_key(self.pid, date)
        if cache_key in products_date_cache:
            return products_date_cache[cache_key]

        if not self.identifs:
            self.get_identificators()
        original = self.get_product(refresh=True)
        prod_copy = productSchemas.ProductResponse(
            id=original.id,
            company_id=original.company_id,
            sku=original.sku,
            name=original.name,
            picture=original.picture,
            last_entry_price=original.last_entry_price,
            price_after_taxes=original.price_after_taxes,
            stock_unit_price=original.stock_unit_price,
            stock=original.stock,
            virtual_stock=original.virtual_stock,
            available_stock=original.available_stock,
            last_entry=original.last_entry,
            last_sell=original.last_sell,
            stock_value=(original.stock or 0) * (self.last_entry_price or 0),
            created_by=original.created_by,
            created_at=original.created_at,
            updated_by=original.updated_by,
            updated_at=original.updated_at,
            identificators=original.identificators,
            supplier=original.supplier
        )
        if not prod_copy.available_stock:
            prod_copy.available_stock = 0
        query = self.db.query(stockModels.StockMovement).filter(stockModels.StockMovement.created_at >= date)\
                .filter(stockModels.StockMovement.product_id == self.pid).all()

        # if prod_copy.sku == '6.ESTIL.PROF.25':
        #     print(prod_copy.sku, prod_copy.available_stock)
        for item in query:
            if item.method:
                prod_copy.available_stock -= item.quantity
            else:
                prod_copy.available_stock += item.quantity
            # if prod_copy.sku == '6.ESTIL.PROF.25':
            #     print(prod_copy.available_stock, item.method, item.quantity)
            if prod_copy.available_stock < 0:
                prod_copy.available_stock = 0

        virtual_query = self.db.query(stockModels.VirtualStockMovements)\
                    .filter(stockModels.VirtualStockMovements.product_id == prod_copy.id)\
                    .filter(stockModels.VirtualStockMovements.location == 'ml_fulfillment')\
                    .filter(stockModels.VirtualStockMovements.created_at <= date)\
                        .order_by(stockModels.VirtualStockMovements.created_at.desc()).first()
        
        if virtual_query:
            prod_copy.virtual_stock = virtual_query.quantity
        else:
            prod_copy.virtual_stock = 0

        prod_copy.stock = prod_copy.virtual_stock + prod_copy.available_stock


        dh_emit = None
        for i in self.identifs:
            if i.code_type == 'supplier_code':
                params = {"cprod": {i.code}, "supplier_cnpj": self.supplier.cnpj, "date_limit": date}
                req = requests.get(f"{API_URL}/invoices/product", params=params)
                if req.status_code == 200:
                    data = req.json()
                    if not data:
                        continue

                    invoice = finantialsSchemas.InvoiceBase.model_validate(data['invoice'])
                    item_inv = finantialsSchemas.InvoiceItemBase.model_validate(data['item'])
                    taxes = finantialsSchemas.TaxesBase.model_validate(data)
                    # events = finantialsSchemas.EventsBase.model_validate(data['events'])
                    if not dh_emit:
                        dh_emit = invoice.dh_emissao

                    p_icms = 0
                    v_icms = 0
                    p_ipi = 0
                    v_ipi = 0

                    new_dh_emit = invoice.dh_emissao
                    if new_dh_emit >= dh_emit:
                        prod_copy.last_entry = new_dh_emit
                        for item in taxes.taxes:
                            if item.item_id != item_inv.id:
                                continue
                            if item.tax == 'ICMS':
                                p_icms = item.p_aliq
                                if not item.p_aliq:
                                    p_icms = 0
                                v_icms = item_inv.v_un_com * (p_icms / 100)
                            
                            elif item.tax == 'IPI':
                                p_ipi = item.p_aliq
                                v_ipi = item_inv.v_un_com * (item.p_aliq / 100)

                            cofins = item_inv.v_un_com * 7.6 / 100
                            pis = item_inv.v_un_com * 1.65 / 100
                            st = 0

                        custo = item_inv.v_un_com - v_icms - pis - cofins + v_ipi + st

                    prod_copy.last_entry_price = item_inv.v_un_com
                    prod_copy.price_after_taxes = custo

        prod_copy.stock_value = prod_copy.stock * prod_copy.last_entry_price
        products_date_cache[cache_key] = prod_copy
        return prod_copy
    
    def get_addresses(self, refresh=False):
        if not hasattr(self, "company_id") or self.company_id is None:
            self._load_product()
        from .stockServices import Address
        from ..models.stockModels import AddressProducts

        self.addresses = productSchemas.ProductAddressResponse()
        self.addresses.product = self.get_product(refresh=refresh)
        query = self.db.query(AddressProducts).filter(AddressProducts.product_id == self.pid).all()
        if query:
            for item in query:
                address = Address(add_id=item.address_id, db=self.db).get_address()
                self.addresses.addresses.append(
                    productSchemas.AddressProduct(
                        quantity=item.quantity,
                        warehouse=address.warehouse,
                        block=address.block,
                        street=address.street,
                        column=address.column,
                        floor=address.floor,
                        address_type=address.address_type,
                        weight_supported=address.weight_supported,
                        weight=address.weight,
                        height=address.height,
                        width=address.width,
                        depth=address.depth,
                        id=address.id,
                        full_address=address.full_address
                    )
                )

        return self.addresses
    
    def _get_last_sell_date(self):
        params = {"cprod": {self.sku}, "supplier_cnpj": self.company.cnpj}
        req = requests.get(f"{API_URL}/invoices/product", params=params)
        if req.status_code == 200:
            data = req.json() 
            if not data:
                return
            invoice = finantialsSchemas.InvoiceBase.model_validate(data['invoice'])
            self.last_sell = invoice.dh_emissao
            

                




