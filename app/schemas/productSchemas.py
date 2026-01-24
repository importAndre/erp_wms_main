from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from .userSchemas import UserResponse

class ProductBase(BaseModel):
    company_id: int
    sku: str
    name: str
    picture: Optional[str] = None
    
class ProductCreate(ProductBase):
    pass

class ProductAddIdentif(BaseModel):
    product_id: int
    code: str
    code_type: Optional[str] = None
    amount: int = 1


class IdentifResponse(ProductAddIdentif):
    created_by: Optional[UserResponse] = None
    created_at: Optional[datetime] = None


class ProductResponse(ProductBase):
    id: Optional[int] = None
    last_entry_price: Optional[float] = None
    price_after_taxes: Optional[float] = None
    stock_unit_price: Optional[float] = None
    stock: Optional[int] = None
    virtual_stock: Optional[int] = None
    available_stock: Optional[int] = None
    created_by: Optional[UserResponse] = None
    created_at: Optional[datetime] = None
    updated_by: Optional[UserResponse] = None
    updated_at: Optional[datetime] = None

class ProductEdit(BaseModel):
    id: int
    company_id: Optional[int] = None
    sku: Optional[str] = None
    name: Optional[str] = None
    picture: Optional[str] = None
