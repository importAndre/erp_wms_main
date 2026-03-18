from ..database import Base
from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, JSON, TIMESTAMP, text

class Company(Base):
    __tablename__ = "DimCompanies"

    id = Column(Integer, primary_key=True, index=True)
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


class User(Base):
    __tablename__ = "DimUsers"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    is_employee = Column(Boolean, default=False)
    employee_id = Column(Integer, nullable=True)


class Employee(Base):
    __tablename__ = "DimEmployees"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone_number = Column(String, nullable=True)
    cpf = Column(String, unique=True, index=True, nullable=False)
    position = Column(String, nullable=True)
    department = Column(String, nullable=True)
    hire_date = Column(String, nullable=True)
    salary = Column(Float, nullable=True)
    cbo = Column(String, nullable=True)
    pis = Column(String, nullable=True)
    ctps = Column(String, nullable=True)
    serie = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    company_id = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey("DimUsers.id"), nullable=True)

class UserPersmissions(Base):
    __tablename__ = "DimUserPermissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("DimUsers.id"), nullable=True)
    permissions = Column(JSON, nullable=False, default='[]')
    updated_by = Column(Integer, ForeignKey('DimUsers.id'), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))
    


from ..database import Base
from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, Date, DateTime, text, UniqueConstraint
from sqlalchemy.orm import relationship


class EmployeePayroll(Base):
    __tablename__ = "FactEmployeePayrolls"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("DimEmployees.id"), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("DimCompanies.id"), nullable=False, index=True)

    ano_referencia = Column(Integer, nullable=False, index=True)
    mes_referencia = Column(Integer, nullable=False, index=True)

    data_competencia = Column(Date, nullable=True)
    data_vencimento = Column(Date, nullable=True)
    data_pagamento = Column(Date, nullable=True)

    salario_base = Column(Float, nullable=True, default=0)
    horas_mensais = Column(Float, nullable=True, default=0)

    base_inss = Column(Float, nullable=True, default=0)
    valor_inss = Column(Float, nullable=True, default=0)
    base_fgts = Column(Float, nullable=True, default=0)
    valor_fgts = Column(Float, nullable=True, default=0)
    base_irrf = Column(Float, nullable=True, default=0)
    valor_irrf = Column(Float, nullable=True, default=0)
    base_rais = Column(Float, nullable=True, default=0)
    base_salario_familia = Column(Float, nullable=True, default=0)

    total_proventos = Column(Float, nullable=False, default=0)
    total_descontos = Column(Float, nullable=False, default=0)
    salario_liquido = Column(Float, nullable=False, default=0)

    status = Column(String, nullable=False, default="pendente")
    paid = Column(Boolean, nullable=False, default=False)
    observacoes = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("now()"), onupdate=text("now()"), nullable=False)

    employee = relationship("Employee")
    items = relationship("EmployeePayrollItem", back_populates="payroll", cascade="all, delete-orphan")

    # __table_args__ = (
    #     UniqueConstraint("employee_id", "ano_referencia", "mes_referencia", name="uq_payroll_employee_mes"),
    # )


class EmployeePayrollItem(Base):
    __tablename__ = "FactEmployeePayrollItems"

    id = Column(Integer, primary_key=True, index=True)
    payroll_id = Column(Integer, ForeignKey("FactEmployeePayrolls.id"), nullable=False, index=True)

    codigo = Column(String, nullable=True)
    descricao = Column(String, nullable=False)
    tipo = Column(String, nullable=False)  # provento ou desconto
    referencia = Column(Float, nullable=True, default=0)
    valor = Column(Float, nullable=False, default=0)

    payroll = relationship("EmployeePayroll", back_populates="items")