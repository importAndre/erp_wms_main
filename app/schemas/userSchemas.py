from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

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
    permissions: Optional[List[str]] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    id: Optional[int] = None
    permissions: Optional[List[str]] = None


class UserPermissionsCreate(BaseModel):
    user_id: int
    permission: str
    add: Optional[bool] = True


class UserTasks(BaseModel):
    task: Optional[str] = None
    date_limit: Optional[datetime] = None


class SuperUserMainPage(BaseModel):

    class Finantials(BaseModel):

        class Revenue(BaseModel):
            revenue: Optional[float] = None
            profit: Optional[float] = None
            to_pay: Optional[float] = None
            stock_value: Optional[float] = None
    
        day_infos: Optional[Revenue] = None
        month_infos: Optional[Revenue] = None
        year_infos: Optional[Revenue] = None


    finantials: Optional[Finantials] = None
    tasks: Optional[List[UserTasks]] = None


class UserMainPage(BaseModel):
    pass

