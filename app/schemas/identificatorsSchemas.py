from pydantic import BaseModel
from typing import Optional

class IdentifBase(BaseModel):
    identif_type: str
    company_id: int
    is_composition: Optional[bool] = False
    product_id: Optional[int] = None
    composition_id: Optional[int] = None
    value: str

class IdentifCreate(IdentifBase):
    pass

class IdentifResponse(IdentifBase):
    pass