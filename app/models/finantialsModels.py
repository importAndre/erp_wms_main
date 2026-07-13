from ..database import Base
from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, JSON, TIMESTAMP, text


class Taxes(Base):
    __tablename__ = 'FactTaxes'

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("DimCompanies.id"), nullable=False)

    transaction_id = Column(
        Integer,
        ForeignKey("FactTransactions.id"),
        nullable=True,
        index=True
    )

    taxes_name = Column(String, nullable=False)
    detail = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    reference = Column(TIMESTAMP)
    payment_date = Column(TIMESTAMP)


class Fixos(Base):
    __tablename__ = 'FactFixos'

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("DimCompanies.id"), nullable=False)

    transaction_id = Column(
        Integer,
        ForeignKey("FactTransactions.id"),
        nullable=True,
        index=True
    )

    name = Column(String, nullable=False)
    detail = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    reference = Column(TIMESTAMP(timezone=True), nullable=True, index=True)
    payment_date = Column(TIMESTAMP)


class Bank(Base):
    __tablename__ = "DimBankAccounts"

    id = Column(Integer, primary_key=True, index=True)

    company_id = Column(Integer, ForeignKey("DimCompanies.id"), nullable=False, index=True)

    bank_name = Column(String(255), nullable=False)
    bank_code = Column(String(20), nullable=True)

    agency = Column(String(50), nullable=True)
    account_number = Column(String(100), nullable=True)
    account_digit = Column(String(20), nullable=True)

    account_type = Column(String(100), nullable=True)
    # exemplos: conta_corrente, conta_pagamento, poupança, mercado_pago

    holder_name = Column(String(255), nullable=True)
    holder_document = Column(String(20), nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(TIMESTAMP(timezone=True), nullable=False)



class TransactionCategories(Base):
    __tablename__ = "DimTransactionCategories"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(255), nullable=False)


class Transactions(Base):
    __tablename__ = "FactTransactions"

    id = Column(Integer, primary_key=True, index=True)

    company_id = Column(Integer, ForeignKey("DimCompanies.id"), nullable=False, index=True)
    bank_account_id = Column(Integer, ForeignKey("DimBankAccounts.id"), nullable=True, index=True)

    # identificação da transação no banco/API
    external_id = Column(String(255), nullable=True, index=True)

    # entrada ou saída
    # True = entrada / crédito
    # False = saída / débito
    method = Column(Boolean, nullable=False)

    # tipo/categoria da transação
    # exemplo: venda, compra, imposto, taxa, folha, transferência, ajuste
    # transaction_type = Column(String(100), nullable=False, index=True)

    category = Column(Integer, ForeignKey("DimTransactionCategories.id"), nullable=True)
    subcategory = Column(String(255), nullable=True)

    description = Column(String, nullable=True)
    detail = Column(String, nullable=True)

    value = Column(Float, nullable=False)

    # data em que a transação aconteceu
    transaction_date = Column(TIMESTAMP(timezone=True), nullable=False, index=True)

    # data de compensação/pagamento, se diferente
    payment_date = Column(TIMESTAMP(timezone=True), nullable=True)

    # referência contábil, ex: mês de competência
    reference = Column(TIMESTAMP(timezone=True), nullable=True, index=True)

    # status da transação
    # exemplo: pending, paid, canceled, refunded
    # status = Column(String(50), nullable=False, server_default=text("'paid'"))

    # origem do dado
    # exemplo: manual, mercado_pago, nubank, itau, bling, mercado_livre
    source = Column(String(100), nullable=True, index=True)

    # vínculos opcionais com outras tabelas
    # order_id = Column(Integer, nullable=True, index=True)
    # invoice_id = Column(Integer, nullable=True, index=True)
    # supplier_id = Column(Integer, nullable=True, index=True)
    # customer_id = Column(Integer, nullable=True, index=True)

    # dados extras crus da API/banco
    # metadata_json = Column(JSON, nullable=True)

    # is_reconciled = Column(Boolean, default=False, nullable=False)
    # is_active = Column(Boolean, default=True, nullable=False)

    counterparty_name = Column(String, nullable=True)
    counterparty_document = Column(String, nullable=True)

    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP")
    )

    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=True,
        onupdate=text("CURRENT_TIMESTAMP")
    )