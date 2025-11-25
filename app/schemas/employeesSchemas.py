from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class EmployeeBase(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    position: Optional[str] = None
    department: Optional[str] = None
    hire_date: Optional[str] = None
    salary: Optional[float] = None
    is_active: Optional[bool] = None
    company_id: Optional[int] = None
    user_id: Optional[int] = None

class EmployeeRegister(EmployeeBase):
    pass

class EmployeeResponse(EmployeeBase):
    pass
    