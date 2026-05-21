from ..database import Base
from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, JSON, TIMESTAMP, text


class Taxes(Base):
    __tablename__ = 'FactTaxes'


    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("DimCompanies.id"), nullable=False)
    taxes_name = Column(String, nullable=False)
    detail = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    reference = Column(TIMESTAMP)
    payment_date = Column(TIMESTAMP)


class Fixos(Base):
    __tablename__ = 'FactFixos'


    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("DimCompanies.id"), nullable=False)
    name = Column(String, nullable=False)
    detail = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    payment_date = Column(TIMESTAMP)


class DimBankAccounts(Base):
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