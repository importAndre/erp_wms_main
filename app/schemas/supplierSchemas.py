from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

class SupplierBase(BaseModel):
    internal_code: Optional[str] = None
    cnpj: Optional[int] = None
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


from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Union

class DupBase(BaseModel):
    nDup: Optional[str] = None
    dVenc: Optional[str] = None
    vDup: Optional[str] = None

class FatBase(BaseModel):
    nFat: Optional[str] = None
    vOrig: Optional[str] = None
    vDesc: Optional[str] = None
    vLiq: Optional[str] = None

class PagamentosBase(BaseModel):
    fat: Optional[FatBase] = None
    dup: Optional[List[DupBase]] = None

    @field_validator("dup", mode="before")
    @classmethod
    def ensure_dup_list(cls, v):
        if v is None:
            return []
        if isinstance(v, dict):
            return [v]
        return v

class SupplierPaymentsBase(BaseModel):
    cnpj_emit: Optional[str] = None
    chave_acesso: Optional[str] = None
    pagamentos: Optional[PagamentosBase] = Field(default=None, alias="pagamentos")

class GetSupplierPayment(BaseModel):
    payments: List[SupplierPaymentsBase] = []


class Payments(BaseModel):
    parcela: Optional[int] = None
    quantidade_parcelas: Optional[int] = None
    valor: Optional[float] = None
    vencimento: Optional[datetime] = None
    supplier: Optional[SupplierResponse] = None

class SupplierPaymentsResponse(BaseModel):
    total: Optional[float] = 0
    quantity: Optional[int] = 0
    notas_pendentes: Optional[int] = 0
    payments: Optional[List[Payments]] = []
