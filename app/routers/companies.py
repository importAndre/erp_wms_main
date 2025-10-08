from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..models.accountModels import Company
from ..schemas import companySchemas
from ..database import get_db

router = APIRouter(
    prefix="/company",
    tags=["company"]
)

@router.post("/register", response_model=companySchemas.CompanyResponse)
def register_company(
    company: companySchemas.CompanyCreate,
    db: Session = Depends(get_db)
) -> companySchemas.CompanyResponse:
    
    existing = db.query(Company).filter(Company.cnpj == company.cnpj).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
        
    new_company = Company(
        cnpj=company.cnpj,
        razao_social=company.razao_social,
        nome_fantasia=company.nome_fantasia,
        data_abertura=company.data_abertura,
        natureza_juridica=company.natureza_juridica,
        situacao=company.situacao,
        situacao_especial=company.situacao_especial,
        tipo_unidade=company.tipo_unidade,
        enquadramento_de_porte=company.enquadramento_de_porte,
        capital_social=company.capital_social,
        opcao_pelo_mei=company.opcao_pelo_mei,
        opcao_pelo_simples=company.opcao_pelo_simples
    )

    db.add(new_company)
    db.commit()
    db.refresh(new_company)

    return new_company