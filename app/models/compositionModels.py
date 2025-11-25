from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint, Float, text
from ..database import Base
from sqlalchemy.sql.sqltypes import TIMESTAMP
from .productModels import Product

class Composition(Base):
    __tablename__ = 'DimCompositions'

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
        UniqueConstraint('company_id', 'sku', name='uq_comp_sku'),
    )


class CompositionItems(Base):
    __tablename__ = 'DimCompositionsItems'

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("DimCompanies.id"), nullable=False)
    composition_id = Column(Integer, ForeignKey("DimCompositions.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("DimProducts.id"), nullable=False)
    amount_required = Column(Float, nullable=True)

    __table_args__ = (
        UniqueConstraint('composition_id', 'product_id', name='uq_composition_product'),
    )

