from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from ..models import orderModels, compositionModels, productModels
from ..schemas import productSchemas, orderSchemas, compositionSchemas
from ..database import get_db, SessionLocal
from ..oauth2 import get_current_user
from ..services import userServices, productServices, compositionServices, orderServices
from datetime import datetime, timedelta
from statistics import mean, median, pstdev
from typing import List, Optional, Dict, Union
import requests
from ..server_config import API_URL
from sqlalchemy import exists
from sqlalchemy import Integer, cast, func
import numpy as np
from tqdm import tqdm


router = APIRouter(
    prefix="/orders",
    tags=["orders"],
    responses={404: {"description": "Not found"}},
)

def get_ml_orders(
    company_id: Optional[int] = 1,
    date_begin: Optional[datetime] = None,
    date_end: Optional[datetime] = None,
) -> List[orderSchemas.OrderPackResponse]:
    db = SessionLocal()
    try:
        from .mercado_livre import get_orders
        if not date_begin:
            date_begin = datetime.now() - timedelta(days=10)
        ml_orders = get_orders(
            company_id=company_id,
            date_begin=date_begin,
            date_end=date_end,
        )

        saved_orders = orderServices.Order.save_ml_orders(ml_orders, db)
        result = []
        loaded_pack_ids = set()
        for saved_order in saved_orders:
            pack_id = saved_order.pack_id or saved_order.order_id
            if pack_id == 'None':
                pack_id = saved_order.order_id
            
            if pack_id in loaded_pack_ids:
                # print(pack_id)
                continue

            loaded_pack_ids.add(pack_id)
            result.append(
                orderServices.Order(
                    pack_id=pack_id,
                    company_id=saved_order.company_id,
                    db=db,
                ).get_order(refresh=False)
            )

        return result
    finally:
        db.close()


def _parse_ml_datetime(value):
    if not value or isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


@router.get("/get-status")
def get_status(
    db: Session = Depends(get_db),
):
    status = (
        db.query(orderModels.Order.status)
        .filter(orderModels.Order.status.isnot(None))
        .distinct()
        .order_by(orderModels.Order.status)
        .all()
    )
    logistics = (
        db.query(orderModels.Order.logistic)
        .filter(orderModels.Order.logistic.isnot(None))
        .distinct()
        .order_by(orderModels.Order.logistic)
        .all()
    )

    return {
        "status": [s for (s,) in status],
        "logistics": [l for (l,) in logistics]
    }

@router.get("/", response_model=orderSchemas.OrderResume)
def get_orders(
    company_id: Optional[int] = 1,
    date_begin: Optional[datetime] = None,
    date_end: Optional[datetime] = None,
    status: Optional[List[str]] = Query(default=None),
    logistic: Optional[List[str]] = Query(default=None),
    refresh: Optional[bool] = False,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    
    if refresh:
        get_ml_orders(
            company_id=company_id,
            date_begin=date_begin,
            date_end=date_end,
        )

    query = db.query(orderModels.Order)

    if company_id is not None:
        query = query.filter(
            orderModels.Order.company_id == company_id
        )

    if date_begin is not None:
        query = query.filter(
            orderModels.Order.created_at >= date_begin
        )

    if date_end is not None:
        query = query.filter(
            orderModels.Order.created_at <= date_end
        )

    if status:
        query = query.filter(
            orderModels.Order.status.in_(status)
        )

    if logistic:
        query = query.filter(
            orderModels.Order.logistic.in_(logistic)
        )
    orders = query.all()
    processed_orders = orderSchemas.OrderResume(
        totals=orderSchemas.OrderTotals(),
        statistics=[]
        )
    processed_orders.totals.total = len(orders)
    numeric_fields = [
        field_name
        for field_name in orderSchemas.OrderTotals.model_fields
        if field_name != "total"
    ]
    values = {field_name: [] for field_name in numeric_fields}
    for item in orders:
        for field_name in numeric_fields:
            value = getattr(item, field_name)
            if value is None:
                continue

            current_total = getattr(processed_orders.totals, field_name)
            setattr(processed_orders.totals, field_name, current_total + value)
            values[field_name].append(value)

        processed_orders.orders.append(
            orderSchemas.OrderResponse(
                id=item.id,
                company_id=item.company_id,
                order_id=item.order_id,
                pack_id=item.pack_id,
                channel=item.channel,
                sku=item.sku,
                quantity=item.quantity,
                logistic=item.logistic,
                total_received=item.total_received,
                shipping_cost=item.shipping_cost,
                shipping_received=item.shipping_received,
                total_amount=item.total_amount,
                sale_fee=item.sale_fee,
                paid_amount=item.paid_amount,
                installments=item.installments,
                payment_id=item.payment_id,
                status=item.status,
                tracking_code=item.tracking_code,
                client_nickname=item.client_nickname,
                shipping_limit=item.shipping_limit,
                shipping_status=item.shipping_status,
                money_release_date=item.money_release_date,
                money_release_status=item.money_release_status,
                created_at=item.created_at,
            )
            )
        
    for field_name in numeric_fields:
        field_values = values[field_name]
        curr = orderSchemas.OrdersStats(
            item=field_name,
            maior_valor=max(field_values) if field_values else 0,
            menor_valor=min(field_values) if field_values else 0,
            media=np.mean(field_values) if field_values else 0,
            mediana=np.median(field_values) if field_values else 0,
            desvio_padrao=np.std(field_values) if field_values else 0,
            variancia=np.var(field_values) if field_values else 0,
            )
        processed_orders.statistics.append(curr)

    return processed_orders




# @router.get("/products")
# def product_sales(
#     company_id: int,
#     product_id: Optional[List[int]] = Query(default=None),
#     date_begin: Optional[datetime] = None,
#     date_end: Optional[datetime] = None,
#     current_user=Depends(get_current_user),
#     db: Session = Depends(get_db),
# ):
#     query = (
#         db.query(
#             orderModels.Order.sku,
#             func.sum(
#                 cast(orderModels.Order.quantity, Integer)
#             ).label("quantity"),
#             func.sum(
#                 orderModels.Order.total_received
#             ).label("total_received"),
#             func.count(
#                 orderModels.Order.id
#             ).label("order_count"),
#         )
#         .filter(orderModels.Order.company_id == company_id)
#         .filter(orderModels.Order.sku.isnot(None))
#     )

#     if product_id:
#         products = (
#             db.query(productModels.Product)
#             .filter(
#                 productModels.Product.company_id == company_id,
#                 productModels.Product.id.in_(product_id),
#             )
#             .all()
#         )

#         composition_ids = (
#             db.query(compositionModels.CompositionItems.composition_id)
#             .filter(compositionModels.CompositionItems.product_id.in_(product_id))
#             .distinct()
#             .all()
#         )
#         composition_ids = [composition_id for (composition_id,) in composition_ids]

#         compositions = (
#             db.query(compositionModels.Composition)
#             .filter(
#                 compositionModels.Composition.company_id == company_id,
#                 compositionModels.Composition.id.in_(composition_ids),
#             )
#             .all()
#         )

#         skus_to_filter = {product.sku for product in products}
#         skus_to_filter.update(composition.sku for composition in compositions)

#         query = query.filter(orderModels.Order.sku.in_(skus_to_filter))
#         print(query)

#     if date_begin is not None:
#         query = query.filter(
#             orderModels.Order.created_at >= date_begin
#         )

#     if date_end is not None:
#         query = query.filter(
#             orderModels.Order.created_at <= date_end
#         )
#     else:
#         query = query.filter(
#             orderModels.Order.created_at <= datetime.now()
#         )

#     rows = (
#         query
#         .group_by(orderModels.Order.sku)
#         .order_by(
#             func.sum(
#                 cast(orderModels.Order.quantity, Integer)
#             ).desc()
#         )
#         .all()
#     )
#     print(rows)
#     for item in rows:
#         print(item)


#     return_data = {}
#     return_data['sales_by_sku'] = [
#             {
#                 "sku": row.sku,
#                 "quantity": row.quantity,
#                 "total_received": row.total_received or 0,
#                 "order_count": row.order_count,
#             }
#             for row in rows
#         ]
    
#     from .products import search_by_sku
#     product_results = {}
#     for item in return_data['sales_by_sku']:
#         product = search_by_sku(sku=item['sku'], db=db)
#         if isinstance(product, productSchemas.ProductResponse):
#             if product.sku not in product_results:
#                 product_results[product.sku] = {
#                     "product_id": product.id,
#                     "quantity": item['quantity'],
#                     "total_received": item['total_received']
#                 }
#             else:
#                 product_results[product.sku]['quantity'] += item['quantity']
#                 product_results[product.sku]['total_received'] += item['total_received']
            
#         elif isinstance(product, compositionSchemas.CompositionResponse):
#             total_items_qt = sum([p.amount_required for p in product.items])
#             # print(product.sku, total_items_qt)
#             for p in product.items:
#                 if p.product.sku not in product_results:
#                     product_results[p.product.sku] = {
#                         "product_id": p.product.id,
#                         "quantity": item['quantity'] * p.amount_required,
#                         "total_received": item['total_received'] * (p.amount_required / total_items_qt)
#                     }
#                     # print(item['total_received'], p.amount_required / total_items_qt, item['total_received'] * (p.amount_required / total_items_qt))
#                 else:
#                     product_results[p.product.sku]['quantity'] += item['quantity'] * p.amount_required
#                     product_results[p.product.sku]['total_received'] += (item['total_received'] * (p.amount_required / total_items_qt))

#     from ..services.finantialServices import Dre
#     dre = Dre(company_id=company_id, date_begin=date_begin, date_end=date_end, db=db).get_dre()
#     taxes_percentage = (dre.deducoes_de_venda.icms + dre.deducoes_de_venda.pis_cofins + dre.deducoes_de_venda.difal) / dre.faturamento

#     for prod, infos in product_results.items():
#         prod_obj = productServices.Product(pid=infos['product_id'], db=db)
#         date_product = prod_obj.get_product_date(date=date_begin)
#         purchases = prod_obj.get_purchases()
#         curr_prod = prod_obj.get_product()
#         infos['revenue_percentage'] = infos['total_received'] / dre.faturamento
#         infos['cmv'] = date_product.stock_value + purchases.v_prod - curr_prod.stock_value
#         infos['cmv_details'] = {
#             "estoque_antigo": date_product.stock_value,
#             "compras": purchases.v_prod,
#             "estoque_atual": curr_prod.stock_value
#         }
#         infos['gross_profit'] = infos['total_received'] - infos['cmv']
#         infos['gross_margin'] = infos['gross_profit'] / infos['total_received']
#         # infos['taxes'] = infos['total_received']

#     return_data['sales_by_product'] = product_results

#     return return_data

    

@router.get("/picking", response_model=orderSchemas.PickingResume)
def get_picking(
    order_id: Optional[str] = None,
    refresh: Optional[bool] = False,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> orderSchemas.PickingResume:
    picking_statuses = list(orderSchemas.StatusResume.model_fields)
    excluded_logistics = ['fulfillment']
    query = (
        db.query(orderModels.Order)
        .filter(orderModels.Order.status.in_(picking_statuses))
        .filter(orderModels.Order.logistic.not_in(excluded_logistics))
    )

    if order_id:
        query = query.filter(
            (orderModels.Order.pack_id == order_id)
            | (orderModels.Order.order_id == order_id)
        )

    rows = query.order_by(orderModels.Order.created_at).all()
    response = orderSchemas.PickingResume()
    logistics = {}
    loaded_packs = set()

    pbar = tqdm(total=len(rows), position=0, leave=True, desc="picking")
    for item in rows:
        pack_id = item.pack_id
        if pack_id == 'None':
            pack_id = item.order_id
        pack_key = (item.company_id, pack_id)
        # if pack_key in loaded_packs:
        #     continue

        loaded_packs.add(pack_key)
        sale = orderServices.Order(
            pack_id=pack_id,
            company_id=item.company_id,
            db=db,
        ).get_order()
        # print(sale.orders[0].order_id)
        if not sale.orders:
            continue

        logistic_name = sale.orders[0].logistic
        logistic = logistics.setdefault(
            logistic_name,
            orderSchemas.LogisticResume(logistic=logistic_name),
        )
        products_quantity = sum(product.quantity or 0 for product in sale.products)

        logistic.total += 1
        logistic.products_quantity += products_quantity
        logistic.sales.append(sale)
        response.total += 1
        response.products_quantity += products_quantity

        sale_statuses = {order.status for order in sale.orders}
        # print('sale_statuses', sale_statuses)
        for sale_status in sale_statuses:
            # print(sale_status)
            if sale_status in picking_statuses:
                current_total = getattr(logistic.status, sale_status)
                setattr(logistic.status, sale_status, current_total + 1)
        # break
        pbar.update(1)

    response.logistics = list(logistics.values())
    return response
    

@router.get("/picking-by-wave")
def get_wave_picking(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    picking_statuses = list(orderSchemas.StatusResume.model_fields)
    excluded_logistics = ['fulfillment']
    query = (
        db.query(orderModels.Order)
        .filter(orderModels.Order.status.in_(picking_statuses))
        .filter(orderModels.Order.logistic.not_in(excluded_logistics))
    ).all()

    processed_skus = []
    for item in query:
        product_query = db.query(productModels.Product).filter(productModels.Product.sku == item.sku).first()
    if product_query:
        prod_obj = productServices.Product(product=product_query, db=db)
        # prod_obj._update_price()
        prod = prod_obj.get_product(refresh=False)
        processed_skus.append(prod.sku)
    composition_query = db.query(compositionModels.Composition).filter(compositionModels.Composition.sku == item.sku).first()
    if composition_query:
        comp_obj = compositionServices.Composition(cid=composition_query.id, db=db)
        # comp_obj.get_comp_entries()
        comp = comp_obj.get_composition(refresh=False)
        processed_skus.append(comp.sku)
        for p in comp.items:
            processed_skus.append(p.product.sku)