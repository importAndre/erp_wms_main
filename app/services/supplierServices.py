from typing import Optional
from ..models import suppliersModels, productModels
from ..schemas import supplierSchemas
from sqlalchemy.orm import Session

# Não armazene instâncias ORM neste cache: elas ficam vinculadas à sessão que
# atendeu a requisição e tornam-se detached quando essa sessão é encerrada.
supplier_cnpjs = {}  # cnpj -> supplier_id

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
        self.products = supplierSchemas.SupplierProductsResponse()

    def _load_supplier(self):
        if self._supplier:
            return

        # tenta cache por CNPJ
        if self.cnpj:
            cached_id = supplier_cnpjs.get(self.cnpj)
            if cached_id is not None and not isinstance(cached_id, int):
                # Descarta entradas criadas pela versão antiga do cache.
                supplier_cnpjs.pop(self.cnpj, None)
                cached_id = None
            query = (
                self.db.query(suppliersModels.Suppliers)
                .filter(
                    suppliersModels.Suppliers.id == cached_id
                    if cached_id is not None
                    else suppliersModels.Suppliers.cnpj == self.cnpj
                )
                .first()
            )
            if not query:
                # O fornecedor pode ter sido removido ou o cache pode estar
                # desatualizado; tenta novamente pelo CNPJ antes de falhar.
                if cached_id is not None:
                    supplier_cnpjs.pop(self.cnpj, None)
                    query = (
                        self.db.query(suppliersModels.Suppliers)
                        .filter(suppliersModels.Suppliers.cnpj == self.cnpj)
                        .first()
                    )
            if not query:
                raise AttributeError("Supplier not found")
            self._supplier = query
            self.sid = query.id
            supplier_cnpjs[query.cnpj] = query.id
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
        supplier_cnpjs[query.cnpj] = query.id

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


    def get_supplier_products(self) -> supplierSchemas.SupplierProductsResponse:
        from .productServices import Product

        self.products = supplierSchemas.SupplierProductsResponse()
        self.products.supplier = self.get_supplier()

        products = self.db.query(productModels.Product).filter(
            productModels.Product.supplier_id == self.sid
        ).all()

        self.products.distinct_products = len(products)

        for p in products:
            product = Product(product=p, db=self.db).get_product()
            self.products.products.append(product)
            self.products.total_stock_value += product.stock_value or 0
            self.products.total_units += product.stock or 0

        return self.products
