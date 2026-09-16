from pydantic import BaseModel, Field
from typing import Optional, List
from .productSchemas import ProductResponse, ProductAddressResponse
from datetime import datetime


class OrderBase(BaseModel):
    id: Optional[int] = None
    company_id: Optional[int] = None
    order_id: Optional[str] = None
    pack_id: Optional[str] = None
    channel: Optional[str] = None
    sku: Optional[str] = None
    quantity: Optional[int] = None
    logistic: Optional[str] = None
    total_received: Optional[float] = None
    shipping_cost: Optional[float] = None
    shipping_received: Optional[float] = None
    total_amount: Optional[float] = None
    sale_fee: Optional[float] = None
    paid_amount: Optional[float] = None
    installments: Optional[int] = None
    payment_id: Optional[int] = None
    status: Optional[str] = None
    tracking_code: Optional[str] = None
    client_nickname: Optional[str] = None
    shipping_limit: Optional[str] = None
    shipping_status: Optional[str] = None
    money_release_date: Optional[datetime] = None
    money_release_status: Optional[str] = None
    created_at: Optional[datetime] = None




class OrderResponse(OrderBase):
    pass


class OrderTotals(BaseModel):
    total: int = 0
    quantity: int = 0
    total_received: float = 0
    shipping_cost: float = 0
    shipping_received: float = 0
    total_amount: float = 0
    sale_fee: float = 0
    paid_amount: float = 0

class OrdersStats(BaseModel):
    item: Optional[str] = None
    maior_valor: float = 0
    menor_valor: float = 0
    media: float = 0
    mediana: float = 0
    desvio_padrao: float = 0
    variancia: float = 0


class OrderResume(BaseModel):
    totals: OrderTotals
    statistics: List[OrdersStats] = Field(default_factory=list)
    orders: List[OrderResponse] = Field(default_factory=list)



class OrderProducts(BaseModel):
    product: Optional[ProductResponse] = None
    quantity: Optional[int] = None
    address: Optional[ProductAddressResponse] = None


class OrderPackResponse(BaseModel):
    orders: List[OrderResponse] = Field(default_factory=list)
    products: List[OrderProducts] = Field(default_factory=list)
    

class StatusResume(BaseModel):
    in_packing_list: Optional[int] = 0
    in_warehouse: Optional[int] = 0
    printed: Optional[int] = 0
    ready_for_pickup: Optional[int] = 0
    ready_to_pack: Optional[int] = 0
    ready_to_print: Optional[int] = 0

class LogisticResume(BaseModel):
    logistic: Optional[str] = None
    total: int = 0
    products_quantity: int = 0
    status: StatusResume = Field(default_factory=StatusResume)
    sales: List[OrderPackResponse] = Field(default_factory=list)


class PickingResume(BaseModel):
    total: int = 0
    products_quantity: int = 0
    logistics: List[LogisticResume] = Field(default_factory=list)

