from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint, Float, text, Boolean, BigInteger
from ..database import Base
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.orm import relationship


class Suppliers(Base):
    __tablename__ = 'DimSuppliers'

    id = Column(Integer, primary_key=True, index=True)
    internal_code = Column(String, unique=True, nullable=True)
    cnpj = Column(BigInteger, unique=True, nullable=True)
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

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("DimCompanies.id"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("DimSuppliers.id"), nullable=True)
    chave_acesso = Column(String, nullable=False)
    parcela = Column(Integer, nullable=True)
    quantidade_parcelas = Column(Integer, nullable=True)
    valor = Column(Float, nullable=True)
    vencimento = Column(TIMESTAMP(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("company_id", "chave_acesso", "parcela", name="uq_supplier_payment_company_chave_parcela"),
    )
