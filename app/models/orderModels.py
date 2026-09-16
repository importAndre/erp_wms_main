from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint, Float, text, BigInteger
from ..database import Base
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.orm import relationship


class Order(Base):
    __tablename__ = "FactOrders"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("DimCompanies.id"), nullable=False)
    order_id = Column(String, nullable=False)
    pack_id = Column(String, nullable=True)
    channel = Column(String, nullable=True)
    sku = Column(String, nullable=True)
    quantity = Column(Integer, nullable=True)
    logistic = Column(String, nullable=True)
    total_received = Column(Float, nullable=True)
    shipping_cost = Column(Float, nullable=True)
    shipping_received = Column(Float, nullable=True)
    total_amount = Column(Float, nullable=True)
    sale_fee = Column(Float, nullable=True)
    paid_amount = Column(Float, nullable=True)
    installments = Column(Integer, nullable=True)
    payment_id = Column(BigInteger, nullable=True)
    status = Column(String, nullable=True)
    tracking_code = Column(String, nullable=True)
    client_nickname = Column(String, nullable=True)
    shipping_limit = Column(String, nullable=True)
    shipping_status = Column(String, nullable=True)
    money_release_date = Column(TIMESTAMP(timezone=True), nullable=True)
    money_release_status = Column(String, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "order_id",
            "sku",
            name="uq_fact_orders_company_order_sku",
        ),
    )







