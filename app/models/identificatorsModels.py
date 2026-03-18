from ..database import Base
from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, UniqueConstraint
from .productModels import Product
from .compositionModels import Composition

class Identificators(Base):
    __tablename__ = "DimIdentificators"

    id = Column(Integer, primary_key=True, index=True)
    identif_type = Column(String, nullable=False)
    company_id = Column(Integer, ForeignKey("DimCompanies.id"), nullable=False)
    is_composition = Column(Boolean, nullable=False, default=False)
    product_id = Column(Integer, ForeignKey('DimProducts.id'), nullable=True)
    composition_id = Column(Integer, ForeignKey('DimCompositions.id'), nullable=True)
    value = Column(String, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            'company_id',
            'identif_type',
            'value',
            'product_id',
            name='uq_comp_itype_value_product'
        ),
    )

