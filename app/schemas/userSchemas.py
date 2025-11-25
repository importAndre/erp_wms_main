from pydantic import BaseModel, EmailStr
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
    id: int
    is_active: bool


class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    id: Optional[int] = None