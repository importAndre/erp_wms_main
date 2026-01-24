from ..models.accountModels import Company as CompanyModel
from ..schemas.companySchemas import CompanyResponse
from sqlalchemy.orm import Session
from ..database import get_db
from fastapi import Depends



class Company:

    def __init__(
            self, 
            company_id: int,
            db: Session = Depends(get_db)
            ):
        self.company_id = company_id
        self._company = None
        self.db = db
        self._load_company()

    def _load_company(self):
        if self._company:
            return self._company
        query = self.db.query(CompanyModel).filter(CompanyModel.id == self.company_id).first()
        self._company = query

    def get_company(self):
        if not self._company:
            self._load_company()
        return CompanyResponse(
            id=self._company.id,
            cnpj=self._company.cnpj,
            razao_social=self._company.razao_social,
            nome_fantasia=self._company.nome_fantasia,
            data_abertura=self._company.data_abertura,
            natureza_juridica=self._company.natureza_juridica,
            situacao=self._company.situacao,
            situacao_especial=self._company.situacao_especial,
            tipo_unidade=self._company.tipo_unidade,
            enquadramento_de_porte=self._company.enquadramento_de_porte,
            capital_social=self._company.capital_social,
            opcao_pelo_mei=self._company.opcao_pelo_mei,
            opcao_pelo_simples=self._company.opcao_pelo_simples,
            inscricao_estadual=self._company.inscricao_estadual
        )


        