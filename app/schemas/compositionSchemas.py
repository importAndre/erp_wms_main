from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from .productSchemas import ProductResponse
from .userSchemas import UserResponse

class CompositionBase(BaseModel):
    company_id: int
    sku: str
    name: Optional[str] = None
    picture: Optional[str] = None


class CompositionCreate(CompositionBase):
    pass

class CompositionItemBase(BaseModel):
    product_id: int
    amount_required: float

class AddCompositionItem(BaseModel):
    composition_id: int
    items: List[CompositionItemBase]


class ItemResponse(BaseModel):
    product: ProductResponse
    amount_required: int

class CompositionResponse(CompositionBase):
    last_entry_price: Optional[float] = None
    price_after_taxes: Optional[float] = None
    stock_unit_price: Optional[float] = None
    stock: Optional[int] = None
    virtual_stock: Optional[int] = None
    available_stock: Optional[int] = None
    created_by: Optional[UserResponse] = None
    updated_by: Optional[UserResponse] = None
    updated_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    items: Optional[List[ItemResponse]] = None