from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from typing import Any, List, Optional
from datetime import datetime
from decimal import Decimal


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


class DetPagBase(BaseModel):
    indPag: Optional[str] = None
    tPag: Optional[str] = None
    vPag: Optional[str] = None


class PagamentosBase(BaseModel):
    fat: Optional[FatBase] = None
    dup: List[DupBase] = Field(default_factory=list)
    detPag: Optional[DetPagBase] = None

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
    id: Optional[int] = None
    company_id: Optional[int] = None
    supplier_id: Optional[int] = None
    transaction_id: Optional[int] = None
    chave_acesso: Optional[str] = None
    numero_nota: Optional[str] = None
    parcela: Optional[int] = None
    quantidade_parcelas: Optional[int] = None
    valor: Optional[float] = None
    vencimento: Optional[datetime] = None
    date_emit: Optional[datetime] = None
    data_pagamento: Optional[datetime] = None
    supplier: Optional[SupplierResponse] = None


class SupplierPaymentsResponse(BaseModel):
    total: float = 0
    quantidade_pagamentos: int = 0
    notas_pendentes: int = 0
    payments: List[Payments] = Field(default_factory=list)


class SupplierPaymentManualCreate(BaseModel):
    company_id: int
    supplier_id: int
    transaction_id: Optional[int] = None
    chave_acesso: str
    numero_nota: str
    parcela: int = Field(default=1, ge=1)
    quantidade_parcelas: int = Field(default=1, ge=1)
    valor: float = Field(ge=0)
    date_emit: Optional[datetime] = None
    vencimento: Optional[datetime] = None
    data_pagamento: Optional[datetime] = None


class SupplierPaymentUpdate(BaseModel):
    company_id: Optional[int] = None
    supplier_id: Optional[int] = None
    transaction_id: Optional[int] = None
    chave_acesso: Optional[str] = None
    numero_nota: Optional[str] = None
    parcela: Optional[int] = Field(default=None, ge=1)
    quantidade_parcelas: Optional[int] = Field(default=None, ge=1)
    valor: Optional[float] = Field(default=None, ge=0)
    date_emit: Optional[datetime] = None
    vencimento: Optional[datetime] = None
    data_pagamento: Optional[datetime] = None


class SupplierPaymentManualResponse(SupplierPaymentManualCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int


class PurchaseBase(BaseModel):
    company_id: Optional[int] = None
    user_id: Optional[int] = None
    category: Optional[str] = None
    asset_name: Optional[str] = None
    c_prod: Optional[str] = None
    seller_cnpj: Optional[str] = None
    numero_nota: Optional[str] = None
    unit_value: Optional[float] = None
    quantity: Optional[int] = None
    total_value: Optional[float] = None
    purchase_date: Optional[datetime] = None


class PurchaseCreate(PurchaseBase):
    pass


class PurchaseResponse(PurchaseBase):
    id: Optional[int] = None
    invoice_id: Optional[int] = None
    transaction_id: Optional[int] = None
    credit_card_id: Optional[int] = None



class SupplierProductsResponse(BaseModel):
    supplier: Optional[SupplierResponse] = None
    total_stock_value: float = 0
    total_units: float = 0
    distinct_products: int = 0
    products: List[Any] = Field(default_factory=list)


class SupplierOrderItemCreate(BaseModel):
    is_composition: bool = False
    product_id: Optional[int] = None
    composition_id: Optional[int] = None
    quantity: int = Field(gt=0)
    check_quantity: float = Field(default=0, ge=0)
    order_price: Decimal = Field(ge=0, max_digits=14, decimal_places=2)

    @model_validator(mode="after")
    def validate_product_reference(self):
        if self.is_composition:
            if self.composition_id is None or self.product_id is not None:
                raise ValueError(
                    "Itens de composição devem informar somente composition_id"
                )
        elif self.product_id is None or self.composition_id is not None:
            raise ValueError(
                "Itens de produto devem informar somente product_id"
            )
        return self


class SupplierOrderItemUpdate(SupplierOrderItemCreate):
    id: Optional[int] = Field(default=None, gt=0)


class SupplierOrderCreate(BaseModel):
    company_id: int
    invoice_id: Optional[int] = None
    supplier_internal_code: str = Field(min_length=1)
    arrived_percent: float = Field(default=0, ge=0, le=100)
    invoice_emit: Optional[datetime] = None
    date_expected: Optional[datetime] = None
    arrived_at: Optional[datetime] = None
    items: List[SupplierOrderItemCreate] = Field(min_length=1)


class SupplierOrderUpdate(BaseModel):
    company_id: Optional[int] = Field(default=None, gt=0)
    invoice_id: Optional[int] = None
    supplier_internal_code: Optional[str] = Field(default=None, min_length=1)
    arrived_percent: Optional[float] = Field(default=None, ge=0, le=100)
    invoice_emit: Optional[datetime] = None
    date_expected: Optional[datetime] = None
    arrived_at: Optional[datetime] = None
    items: Optional[List[SupplierOrderItemUpdate]] = Field(
        default=None,
        min_length=1,
    )

    @model_validator(mode="after")
    def validate_update_fields(self):
        if not self.model_fields_set:
            raise ValueError("Informe ao menos um campo para atualizar")
        if self.items is not None:
            item_ids = [item.id for item in self.items if item.id is not None]
            if len(item_ids) != len(set(item_ids)):
                raise ValueError("Um item não pode ser informado mais de uma vez")
        return self


class SupplierOrderItemResponse(SupplierOrderItemCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int


class SupplierOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    invoice_id: Optional[int] = None
    supplier_internal_code: str
    arrived_percent: float
    invoice_emit: Optional[datetime] = None
    date_expected: Optional[datetime] = None
    arrived_at: Optional[datetime] = None
    created_at: datetime
    items: List[SupplierOrderItemResponse] = Field(default_factory=list)
