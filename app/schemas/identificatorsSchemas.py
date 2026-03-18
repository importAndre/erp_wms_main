from pydantic import BaseModel
from typing import Optional

class IdentifBase(BaseModel):
    identif_type: Optional[str] = None
    company_id: Optional[int] = None
    is_composition: Optional[bool] = False
    product_id: Optional[int] = None
    composition_id: Optional[int] = None
    value: Optional[str] = None

class IdentifCreate(IdentifBase):
    pass

class IdentifResponse(IdentifBase):
    id: Optional[int] = None