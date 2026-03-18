from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class EmployeeBase(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    cpf: Optional[str] = None
    position: Optional[str] = None
    department: Optional[str] = None
    hire_date: Optional[str] = None
    salary: Optional[float] = None
    cbo: Optional[str] = None
    pis: Optional[str] = None
    ctps: Optional[str] = None
    serie: Optional[int] = None
    is_active: Optional[bool] = None
    company_id: Optional[int] = None
    user_id: Optional[int] = None


class EmployeeRegister(EmployeeBase):
    pass


class EmployeeResponse(EmployeeBase):
    id: Optional[int] = None

    class Config:
        orm_mode = True

class EmployeePayrollItemBase(BaseModel):
    codigo: Optional[str] = None
    descricao: str
    tipo: str
    referencia: Optional[float] = 0
    valor: float


class EmployeePayrollItemCreate(EmployeePayrollItemBase):
    pass


class EmployeePayrollItemResponse(EmployeePayrollItemBase):
    id: int

    class Config:
        orm_mode = True


class EmployeePayrollBase(BaseModel):
    employee_id: int
    company_id: int
    ano_referencia: int
    mes_referencia: int
    data_competencia: Optional[datetime] = None
    data_vencimento: Optional[datetime] = None
    data_pagamento: Optional[datetime] = None
    salario_base: Optional[float] = 0
    horas_mensais: Optional[float] = 0
    base_inss: Optional[float] = 0
    valor_inss: Optional[float] = 0
    base_fgts: Optional[float] = 0
    valor_fgts: Optional[float] = 0
    base_irrf: Optional[float] = 0
    valor_irrf: Optional[float] = 0
    base_rais: Optional[float] = 0
    base_salario_familia: Optional[float] = 0
    total_proventos: Optional[float] = 0
    total_descontos: Optional[float] = 0
    salario_liquido: Optional[float] = 0
    status: Optional[str] = "pendente"
    paid: Optional[bool] = False
    observacoes: Optional[str] = None


class EmployeePayrollCreate(EmployeePayrollBase):
    items: List[EmployeePayrollItemCreate] = []


class EmployeePayrollResponse(EmployeePayrollBase):
    id: int
    employee: Optional[EmployeeResponse] = None
    items: List[EmployeePayrollItemResponse] = []

    class Config:
        orm_mode = True