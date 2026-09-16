from ..models import orderModels, productModels, compositionModels
from sqlalchemy.orm import Session
from ..database import get_db
from fastapi import Depends
from .userServices import User
from typing import Optional
from ..schemas import orderSchemas
from .productServices import Product
from .compositionServices import Composition
from datetime import datetime


class Order:
    def __init__(
            self,
            pack_id: str,
            company_id: int = 1,
            db: Session = Depends(get_db)
            ):
        self.db = db
        self.pack_id = str(pack_id)
        self.company_id = company_id
        self.order = orderSchemas.OrderPackResponse()
        self.updated = False

        self._load_order()


    def _load_order(self, refresh=False):
        self.order = orderSchemas.OrderPackResponse()
        query = (
            self.db.query(orderModels.Order)
            .filter(
                orderModels.Order.company_id == self.company_id,
                orderModels.Order.pack_id == self.pack_id,
            )
            .all()
        )
        if not query:
            query = (
                self.db.query(orderModels.Order)
                .filter(
                    orderModels.Order.company_id == self.company_id,
                    orderModels.Order.order_id == self.pack_id,
                )
                .all()
            )

        if not query or refresh:
            ml_orders = self._search_order(self.pack_id)
            self.save_ml_orders(ml_orders, self.db)
            query = (
                self.db.query(orderModels.Order)
                .filter(
                    orderModels.Order.company_id == self.company_id,
                    (
                        (orderModels.Order.pack_id == self.pack_id)
                        | (orderModels.Order.order_id == self.pack_id)
                    ),
                )
                .all()
            )


        for o in query:
            self.order.orders.append(
                orderSchemas.OrderResponse(
                    id=o.id,
                    company_id=o.company_id,
                    order_id=o.order_id,
                    pack_id=o.pack_id,
                    channel=o.channel,
                    sku=o.sku,
                    quantity=o.quantity,
                    logistic=o.logistic,
                    total_received=o.total_received,
                    shipping_cost=o.shipping_cost,
                    shipping_received=o.shipping_received,
                    total_amount=o.total_amount,
                    sale_fee=o.sale_fee,
                    paid_amount=o.paid_amount,
                    installments=o.installments,
                    payment_id=o.payment_id,
                    status=o.status,
                    tracking_code=o.tracking_code,
                    client_nickname=o.client_nickname,
                    shipping_limit=o.shipping_limit,
                    shipping_status=o.shipping_status,
                    money_release_date=o.money_release_date,
                    money_release_status=o.money_release_status,
                    created_at=o.created_at,
                )
            )
        
        self._load_products()
        self.updated = True


    def _load_products(self):
        for item in self.order.orders:
            product_query = self.db.query(productModels.Product).filter(productModels.Product.sku == item.sku).first()
            if product_query:
                prod_obj = Product(product=product_query, db=self.db)
                # prod_obj._update_price()
                self.order.products.append(
                    orderSchemas.OrderProducts(
                        product=prod_obj.get_product(),
                        quantity=item.quantity,
                        address=prod_obj.get_addresses()
                    )
                ) 
            else:
                composition_query = self.db.query(compositionModels.Composition).filter(compositionModels.Composition.sku == item.sku).first()
                if not composition_query:
                    print(f'Product {item.sku} not found')
                    continue
                comp_obj = Composition(cid=composition_query.id, db=self.db)
                comp = comp_obj.get_composition()

                for p in comp.items:
                    curr_prod = Product(pid=p.product.id, db=self.db)
                    self.order.products.append(
                        orderSchemas.OrderProducts(
                            product=curr_prod.get_product(),
                            address=curr_prod.get_addresses(),
                            quantity=item.quantity * p.amount_required
                        )
                    )

    def get_order(self, refresh=False):
        if not self.updated or refresh:
            self._load_order(refresh=refresh)
        return self.order
    
    def _search_order(self, order_id):
        from .mercadoLivreServices import MercadoLivreOrder

        order = MercadoLivreOrder(
            order_id=order_id,
            cid=self.company_id,
        )
        return order.get_order()

    @staticmethod
    def _parse_ml_datetime(value):
        if not value or isinstance(value, datetime):
            return value
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    @classmethod
    def save_ml_orders(cls, orders, db):
        if orders is None:
            return []
        if not isinstance(orders, list):
            orders = [orders]

        result = []
        pending_orders = {}

        for order in orders:
            order_id = str(order.order_id)
            pack_id = str(order.pack_id) if order.pack_id else order_id
            order_status = (
                "shipped" if order.substatus == "in_hub" else order.substatus
            )
            order_data = {
                "company_id": order.company_id,
                "order_id": order_id,
                "pack_id": pack_id,
                "channel": "mercado_livre",
                "sku": order.sku,
                "quantity": order.quantity,
                "logistic": order.logistic_type,
                "total_received": order.total_received,
                "shipping_cost": order.shipping_cost,
                "shipping_received": order.shipping_received,
                "total_amount": order.total_amount,
                "sale_fee": order.sale_fee,
                "paid_amount": order.paid_amount,
                "installments": order.installments,
                "payment_id": order.payment_id,
                "status": order_status,
                "tracking_code": order.tracking_number,
                "client_nickname": order.client_nickname,
                "shipping_limit": order.shipping_limit,
                "shipping_status": order.shipping_status,
                "money_release_date": cls._parse_ml_datetime(
                    order.money_release_date
                ),
                "money_release_status": order.money_release_status,
                "created_at": cls._parse_ml_datetime(order.date_created),
            }
            order_key = (order.company_id, order_id, order.sku)
            saved_order = pending_orders.get(order_key)

            if saved_order is None:
                saved_order = (
                    db.query(orderModels.Order)
                    .filter(
                        orderModels.Order.company_id == order.company_id,
                        orderModels.Order.order_id == order_id,
                        orderModels.Order.sku == order.sku,
                    )
                    .first()
                )

            if saved_order is None:
                saved_order = orderModels.Order(**order_data)
                db.add(saved_order)
                pending_orders[order_key] = saved_order
            else:
                for field, value in order_data.items():
                    if getattr(saved_order, field) != value:
                        setattr(saved_order, field, value)

            result.append(saved_order)

        db.commit()
        for saved_order in result:
            db.refresh(saved_order)
        return result
    


                




        

