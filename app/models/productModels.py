from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint, Float, text
from ..database import Base
from sqlalchemy.sql.sqltypes import TIMESTAMP


class Product(Base):
    __tablename__ = "DimProducts"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("DimCompanies.id"), nullable=False)
    sku = Column(String, nullable=False)
    name = Column(String, nullable=False)
    last_entry_price = Column(Float, nullable=True)
    price_after_taxes = Column(Float, nullable=True)
    stock_unit_price = Column(Float, nullable=True)
    stock = Column(Integer, nullable=True)
    virtual_stock = Column(Integer, nullable=True)
    available_stock = Column(Integer, nullable=True)
    picture = Column(String, nullable=True)
    created_by = Column(Integer, ForeignKey('DimUsers.id'), nullable=False)
    updated_by = Column(Integer, ForeignKey('DimUsers.id'), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()')) 


    __table_args__ = (
        UniqueConstraint('company_id', 'sku', name='uq_company_sku'),
    )
