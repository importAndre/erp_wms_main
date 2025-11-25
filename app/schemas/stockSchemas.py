from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from .userSchemas import UserResponse
from.productSchemas import ProductResponse

class AddressBase(BaseModel):
    warehouse: str
    block: str
    street: str
    column: str
    floor: str
    address_type: str
    weight_supported: Optional[float] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    width: Optional[float] = None
    depth: Optional[float] = None


class AddressCreate(AddressBase):
    pass

class AddressResponse(AddressBase):
    id: int
    full_address: str

class AddressItemResponse(BaseModel):
    product: ProductResponse
    quantity: int

class AddressProductsResponse(BaseModel):
    address: AddressResponse
    products: List[AddressItemResponse]

class StockMovementBase(BaseModel):
    address_id: int
    product_id: int
    method: bool
    quantity: int
    motive: Optional[str] = None
    motive_link: Optional[str] = None

class StockMovementCreate(StockMovementBase):
    pass

class StockMovementResponse(StockMovementBase):
    id: int
    created_by: UserResponse
    created_at: datetime