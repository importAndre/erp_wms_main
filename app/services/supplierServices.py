from typing import Optional
from ..models import suppliersModels
from ..schemas import supplierSchemas
from sqlalchemy.orm import Session

supplier_cnpjs = {}  # cnpj -> suppliersModels.Suppliers

class Supplier:
    def __init__(
        self,
        db: Session,
        sid: Optional[int] = None,
        cnpj: Optional[str] = None,
        supplier: Optional[suppliersModels.Suppliers] = None,
    ):
        self.sid = sid if sid is not None else (supplier.id if supplier else None)
        self.cnpj = cnpj if cnpj is not None else (supplier.cnpj if supplier else None)
        self._supplier = supplier
        self.db = db
        self._load_supplier()

    def _load_supplier(self):
        if self._supplier:
            return

        # tenta cache por CNPJ
        if self.cnpj:
            cached = supplier_cnpjs.get(self.cnpj)
            if cached:
                self._supplier = cached
                self.sid = cached.id
                return

            # fallback banco
            query = (
                self.db.query(suppliersModels.Suppliers)
                .filter(suppliersModels.Suppliers.cnpj == self.cnpj)
                .first()
            )
            if not query:
                raise AttributeError("Supplier not found")
            self._supplier = query
            self.sid = query.id
            supplier_cnpjs[query.cnpj] = query
            return

        # busca por id
        if self.sid is None:
            raise ValueError("Você deve informar sid, cnpj ou supplier.")

        query = (
            self.db.query(suppliersModels.Suppliers)
            .filter(suppliersModels.Suppliers.id == self.sid)
            .first()
        )
        if not query:
            raise AttributeError("Supplier not found")

        self._supplier = query
        self.cnpj = query.cnpj
        supplier_cnpjs[query.cnpj] = query

    def get_supplier(self):
        if not self._supplier:
            self._load_supplier()

        s = self._supplier
        return supplierSchemas.SupplierResponse(
            id=s.id,
            internal_code=s.internal_code,
            cnpj=s.cnpj,
            razao_social=s.razao_social,
            nome_fantasia=s.nome_fantasia,
            data_abertura=s.data_abertura,
            natureza_juridica=s.natureza_juridica,
            situacao=s.situacao,
            situacao_especial=s.situacao_especial,
            tipo_unidade=s.tipo_unidade,
            enquadramento_de_porte=s.enquadramento_de_porte,
            capital_social=s.capital_social,
            opcao_pelo_mei=s.opcao_pelo_mei,
            opcao_pelo_simples=s.opcao_pelo_simples,
            inscricao_estadual=s.inscricao_estadual
        )
