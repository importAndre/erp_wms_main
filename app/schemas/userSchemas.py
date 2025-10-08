from pydantic import BaseModel
from typing import List, Optional

class UserBase(BaseModel):
    username: str
    email: str
    is_superuser: bool
    is_employee: bool
    employee_id: Optional[int] = None


class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    is_active: bool