from __future__ import annotations

from pydantic import BaseModel, Field, field_validator
from typing import Any, List, Optional
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
    dup: List[DupBase] = Field(default_factory=list)

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
    numero_nota: Optional[str] = None
    pagamentos: Optional[PagamentosBase] = Field(default=None, alias="pagamentos")
    date_emit: Optional[datetime] = None


class GetSupplierPayment(BaseModel):
    payments: List[SupplierPaymentsBase] = Field(default_factory=list)


class Payments(BaseModel):
    numero_nota: Optional[str] = None
    parcela: Optional[int] = None
    quantidade_parcelas: Optional[int] = None
    valor: Optional[float] = None
    vencimento: Optional[datetime] = None
    date_emit: Optional[datetime] = None
    supplier: Optional[SupplierResponse] = None


class SupplierPaymentsResponse(BaseModel):
    total: float = 0
    quantidade_pagamentos: int = 0
    notas_pendentes: int = 0
    payments: List[Payments] = Field(default_factory=list)


class PurchaseBase(BaseModel):
    company_id: Optional[int] = None
    user_id: Optional[int] = None
    category: Optional[str] = None
    asset_name: Optional[str] = None
    c_prod: Optional[str] = None
    seller_cnpj: Optional[str] = None
    numero_nota: Optional[str] = None


class PurchaseCreate(PurchaseBase):
    pass


class PurchaseResponse(PurchaseBase):
    id: Optional[int] = None
    invoice_id: Optional[int] = None
    quantity: Optional[int] = None
    unit_value: Optional[float] = None
    total_value: Optional[float] = None
    purchase_date: Optional[datetime] = None


class SupplierProductsResponse(BaseModel):
    supplier: Optional[SupplierResponse] = None
    total_stock_value: float = 0
    total_units: float = 0
    distinct_products: int = 0
    products: List[Any] = Field(default_factory=list)
