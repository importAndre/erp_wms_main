from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint, Float, text, Boolean, BigInteger
from ..database import Base
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.orm import relationship


class Suppliers(Base):
    __tablename__ = 'DimSuppliers'

    id = Column(Integer, primary_key=True, index=True)
    internal_code = Column(String, nullable=True)
    cnpj = Column(String, unique=True, nullable=True)
    razao_social = Column(String, nullable=True)
    nome_fantasia = Column(String, nullable=True)
    data_abertura = Column(String, nullable=True)
    natureza_juridica = Column(String, nullable=True)
    situacao = Column(String, nullable=True)
    situacao_especial = Column(String, nullable=True)
    tipo_unidade = Column(String, nullable=True)
    enquadramento_de_porte = Column(String, nullable=True)
    capital_social = Column(Float, nullable=True)
    opcao_pelo_mei = Column(Boolean, nullable=True)
    opcao_pelo_simples = Column(Boolean, nullable=True)
    inscricao_estadual = Column(String, nullable=True)


class SupplierPayments(Base):
    __tablename__ = 'FactSupplierPayments'

    transaction_id = Column(
        Integer,
        ForeignKey("FactTransactions.id"),
        nullable=True,
        index=True
    )

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("DimCompanies.id"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("DimSuppliers.id"), nullable=True)
    chave_acesso = Column(String, nullable=False)
    date_emit = Column(TIMESTAMP(timezone=True), nullable=True)
    numero_nota = Column(String, nullable=False)
    parcela = Column(Integer, nullable=True)
    quantidade_parcelas = Column(Integer, nullable=True)
    valor = Column(Float, nullable=True)
    vencimento = Column(TIMESTAMP(timezone=True), nullable=True)
    data_pagamento = Column(TIMESTAMP(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("company_id", "chave_acesso", "parcela", name="uq_supplier_payment_company_chave_parcela"),
    )


class Purchases(Base):
    __tablename__ = 'FactPurchases'

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("DimCompanies.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("DimUsers.id"), nullable=False)
    invoice_id = Column(Integer, nullable=True)
    category = Column(String, nullable=False)
    asset_name = Column(String, nullable=False)
    c_prod = Column(String, nullable=False)
    seller_cnpj = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_value = Column(Float, nullable=False)
    total_value = Column(Float, nullable=False)
    purchase_date = Column(TIMESTAMP(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("invoice_id", "c_prod", "quantity", "company_id", name='uq_inv_prod_qt_cid'),
    )


class SupplierOrders(Base):
    __tablename__ = 'FactSupplierOrders'

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("DimCompanies.id"), nullable=False)
    invoice_id = Column(Integer, nullable=True)
    supplier_internal_code = Column(String, nullable=False)
    arrived_percent = Column(Float, nullable=False, default=0)
    invoice_emit = Column(TIMESTAMP(timezone=True), nullable=True)
    date_expected = Column(TIMESTAMP(timezone=True), nullable=True)
    arrived_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

    items = relationship("SupplierOrderItems", back_populates="order", cascade="all, delete-orphan")


class SupplierOrderItems(Base):
    __tablename__ = 'FactSupplierOrderItems'

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("FactSupplierOrders.id"), nullable=False)
    is_composition = Column(Boolean, default=False)
    product_id = Column(Integer, ForeignKey("DimProducts.id"), nullable=True)
    composition_id = Column(Integer, ForeignKey("DimCompositions.id"), nullable=True)
    quantity = Column(Integer)
    check_quantity = Column(Float, default=0)

    order = relationship("SupplierOrders", back_populates="items")

