from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CompanyBase(BaseModel):
    cnpj: str
    razao_social: str
    nome_fantasia: Optional[str] = None
    data_abertura: datetime
    natureza_juridica: Optional[str] = None
    situacao: Optional[str] = None
    situacao_especial: Optional[str] = None
    tipo_unidade: Optional[str] = None
    enquadramento_de_porte: Optional[str] = None
    capital_social: Optional[float] = None
    opcao_pelo_mei: Optional[bool] = None
    opcao_pelo_simples: Optional[bool] = None
    inscricao_estadual: Optional[str] = None

class CompanyCreate(CompanyBase):
    pass

class CompanyResponse(CompanyBase):
    pass