from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class VirtualStock(BaseModel):
    sku: str
    quantity: int
    last_update: Optional[datetime] = None

class PriceUpdate(BaseModel):
    chave_nfe: str
    c_prod: str

class ToDo(BaseModel):
    source: str
    task: str
