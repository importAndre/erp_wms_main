from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean
from sqlalchemy.sql.sqltypes import TIMESTAMP
from ..database import Base

class Address(Base):
    __tablename__ = "DimAddresses"

    id = Column(Integer, primary_key=True, index=True)
    warehouse = Column(String, nullable=False)
    block = Column(String, nullable=False)
    street = Column(String, nullable=False)
    column = Column(String, nullable=False)
    floor = Column(String, nullable=False)
    full_address = Column(String, nullable=False, unique=True)
    address_type = Column(String, nullable=False)
    weight_supported = Column(Float, nullable=True)
    weight = Column(Float, nullable=True, default=0.0)
    height = Column(Float, nullable=True)
    width = Column(Float, nullable=True)
    depth = Column(Float, nullable=True)


class StockMovement(Base):
    __tablename__ = "FactStockMovements"

    id = Column(Integer, primary_key=True, index=True)
    address_id = Column(Integer, ForeignKey("DimAddresses.id"), nullable=False)
    method = Column(Boolean, nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    motive = Column(String, nullable=True)
    motive_link = Column(Integer, nullable=True)
    created_by = Column(Integer, ForeignKey("DimUsers.id"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default='now()')


class AddressProducts(Base):
    __tablename__ = "DimAddressProducts"

    id = Column(Integer, primary_key=True, index=True)
    address_id = Column(Integer, ForeignKey("DimAddresses.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("DimProducts.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=0)
    updated_at = Column(TIMESTAMP(timezone=True), server_default='now()')
    