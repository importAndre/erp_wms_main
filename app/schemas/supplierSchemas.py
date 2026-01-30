from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

class SupplierBase(BaseModel):
    internal_code: Optional[str] = None
    cnpj: Optional[str] = None
    razao_social: Optional[str] = None
    nome_fantasia: Optional[str] = None
    data_abertura: Optional[str] = None
    natureza_juridica: Optional[str] = None
    situacao: Optional[str] = None
    situacao_especial: Optional[str] = None
    tipo_unidade: Optional[str] = None
    enquadramento_de_porte: Optional[str] = None
    capital_social: Optional[float] = None
    opcao_pelo_mei: Optional[bool] = None
    opcao_pelo_simples: Optional[bool] = None
    inscricao_estadual: Optional[str] = None

class SupplierCreate(SupplierBase):
    pass

class SupplierResponse(SupplierBase):
    id: Optional[int] = None