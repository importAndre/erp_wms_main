from pydantic import BaseModel
from typing import List, Optional

class ProductBase(BaseModel):
    company_id: int
    sku: str
    name: str
    picture: Optional[str] = None
    
class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    last_entry_price: Optional[float] = None
    price_after_taxes: Optional[float] = None
    stock_unit_price: Optional[float] = None
    stock: Optional[int] = None
    virtual_stock: Optional[int] = None
    available_stock: Optional[int] = None
    created_by: Optional[float] = None
    created_at: Optional[float] = None
    updated_by: Optional[float] = None
    updated_at: Optional[float] = None