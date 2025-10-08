from ..database import Base
from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey

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
    incricao_estadual = Column(String, nullable=True)


class User(Base):
    __tablename__ = "DimUsers"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    is_employee = Column(Boolean, default=False)
    employee_id = Column(Integer, nullable=True)  # Foreign key to Employee.id


class Employee(Base):
    __tablename__ = "DimEmployees"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone_number = Column(String, unique=True, index=True, nullable=False)
    position = Column(String, nullable=True)
    department = Column(String, nullable=True)
    hire_date = Column(String, nullable=True)
    salary = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True)
    company_id = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey("DimUsers.id"), nullable=True)

