from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint, Float, text, Boolean
from ..database import Base
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.orm import relationship


class Suppliers(Base):
    __tablename__ = 'DimSuppliers'

    id = Column(Integer, primary_key=True, index=True)
    internal_code = Column(String, unique=True, nullable=True)
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

