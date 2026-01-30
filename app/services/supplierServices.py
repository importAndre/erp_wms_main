from typing import Optional
from ..models import suppliersModels
from ..schemas import supplierSchemas
from sqlalchemy.orm import Session
from ..database import get_db
from fastapi import Depends

class Supplier:

    def __init__(
        self,
        sid: Optional[int] = None,
        supplier: Optional[suppliersModels.Suppliers] = None,
        db: Session = Depends(get_db)
        ):
        self.sid = sid if sid else supplier.id
        self._supplier = supplier if supplier else None
        self.db = db

    def _load_supplier(self):
        if self._supplier:
            return
        query = self.db.query(suppliersModels.Suppliers).filter(suppliersModels.Suppliers.id == self.sid).first()
        if not query:
            raise AttributeError("User not found")
        self._supplier = query

    def get_supplier(self):
        if not self._supplier:
            self._load_supplier()
        return supplierSchemas.SupplierResponse(
            id=self._supplier.id,
            internal_code=self._supplier.internal_code,
            cnpj=self._supplier.cnpj,
            razao_social=self._supplier.razao_social,
            nome_fantasia=self._supplier.nome_fantasia,
            data_abertura=self._supplier.data_abertura,
            natureza_juridica=self._supplier.natureza_juridica,
            situacao=self._supplier.situacao,
            situacao_especial=self._supplier.situacao_especial,
            tipo_unidade=self._supplier.tipo_unidade,
            enquadramento_de_porte=self._supplier.enquadramento_de_porte,
            capital_social=self._supplier.capital_social,
            opcao_pelo_mei=self._supplier.opcao_pelo_mei,
            opcao_pelo_simples=self._supplier.opcao_pelo_simples,
            inscricao_estadual=self._supplier.inscricao_estadual
        )        





       