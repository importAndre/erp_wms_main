from ..database import get_db
from fastapi import Depends
from sqlalchemy.orm import Session
from ..schemas import finantialsSchemas, mercadoLivreSchemas, supplierSchemas, productSchemas, compositionSchemas
from datetime import date, datetime, timedelta, time
from calendar import monthrange
from ..models import productModels, suppliersModels, accountModels, finantialsModels, compositionModels
from ..server_config import API_URL
from .companyServices import Company
from .productServices import Product
from .compositionServices import Composition
from .supplierServices import Supplier
from .employeeServices import Employee
import requests
from typing import Union, List
from tqdm import tqdm



def normalize_period(date_begin: date, date_end: date):
    if isinstance(date_begin, datetime):
        date_begin = date_begin.date()

    if isinstance(date_end, datetime):
        date_end = date_end.date()

    if date_end < date_begin:
        raise ValueError("date_end não pode ser menor que date_begin.")

    return date_begin, date_end


def start_of_day(value: date):
    return datetime.combine(value, time.min)


def end_of_day(value: date):
    return datetime.combine(value, time.max)


def get_product(sku: str, db: Session = Depends(get_db)) -> Union[productSchemas.ProductResponse, compositionSchemas.CompositionResponse]:
    product_query = db.query(productModels.Product).filter(productModels.Product.sku == sku).first()
    if product_query:
        return Product(product=product_query, db=db).get_product()
    composition_query = db.query(compositionModels.Composition).filter(compositionModels.Composition.sku == sku).first()
    if composition_query:
        return Composition(cid=composition_query.id, db=db).get_composition()
    return None


# class PatrominialBalance:
#     def __init__(
#         self,
#         company_id: int,
#         date_begin: date,
#         date_end: date,
#         db: Session = Depends(get_db)
#     ):
#         self.company_id = company_id
#         self.db = db

#         self.date_begin, self.date_end = normalize_period(date_begin, date_end)
#         self.date_begin_dt = start_of_day(self.date_begin)
#         self.date_end_dt = end_of_day(self.date_end)

#         self.balance = None
#         self.company = Company(company_id=company_id, db=db).get_company()
#         self.ativo_circulante = finantialsSchemas.AtivoCirculante()
#         self.ativos_nao_circulantes = finantialsSchemas.AtivoNaoCirculante()
#         self.ativo = finantialsSchemas.Ativo()

    
#     def _get_full_stocks(self):
#         url = f"{API_URL}/mercado-livre/listings/full-stock"
#         params = {
#             "company_id": self.company.id,
#             "date": self.date_end
#         }
#         req = requests.get(url=url, params=params)
#         if req.status_code == 200:
#             data = req.json()
#             pbar = tqdm(total=len(data), position=0, leave=True, desc='Full Stock', unit='prod')
#             for item in data:
#                 prod = get_product(sku=item, db=self.db)
#                 pbar.update(1)
#                 if not prod or not prod.last_entry_price:
#                     # print(f'not price for {item}')
#                     continue
#                 self.ativo_circulante.estoque += prod.last_entry_price * data[item]


#     def _load_ativos(self):

#         self._get_full_stocks()

#         products = self.db.query(productModels.Product).filter(productModels.Product.company_id == self.company_id).all()
#         pbar = tqdm(total=len(products), position=0, leave=True, desc='Product Stock', unit='prod')
#         for p in products:
#             prod = Product(product=p, db=self.db)
#             product_info = prod.get_product()

#             if not product_info.last_entry_price:
#                 pbar.update(1)
#                 continue

#             stock_at_date = prod.get_product_date(date=self.date_end)

#             self.ativo_circulante.estoque += (
#                 stock_at_date * product_info.last_entry_price
#             )

#             pbar.update(1)


#         categories = ['estrutura']
#         imobilizado_query = self.db.query(suppliersModels.Purchases).filter(suppliersModels.Purchases.purchase_date <= self.date_end)\
#                             .filter(suppliersModels.Purchases.category.in_(categories)).all()
#         for imo in imobilizado_query:
#             self.ativos_nao_circulantes.imobilizado += imo.total_value
#             self.ativos_nao_circulantes.imobilizado_detail.append(
#                 finantialsSchemas.ImobilizadoDetail(
#                     item=imo.asset_name,
#                     value=imo.total_value
#                 )
#             )

#         self.ativo.ativos_circulantes = self.ativo_circulante
#         self.ativo.ativos_nao_circulantes = self.ativos_nao_circulantes

#         self.ativo.total_ativo_circulante = self.ativo_circulante.estoque + self.ativo_circulante.caixa + self.ativo_circulante.aplicacoes + self.ativo_circulante.contas_a_receber + self.ativo_circulante.impostos_a_recuperar + self.ativo_circulante.outros_creditos
#         self.ativo.total_ativo_nao_circulante = self.ativos_nao_circulantes.aplicacoes_financeiras + self.ativos_nao_circulantes.contas_a_receber + self.ativos_nao_circulantes.impostos_a_recuperar + self.ativos_nao_circulantes.outros_creditos + self.ativos_nao_circulantes.imobilizado + self.ativos_nao_circulantes.intangivel

#         self.ativo.total_ativo = self.ativo.total_ativo_circulante + self.ativo.total_ativo_nao_circulante


#     def _load_passivos(self):
#         passivos_circulante = finantialsSchemas.PassivoCirculante()
#         passivos_nao_circulante = finantialsSchemas.PassivoNaoCirculante()
#         passivo = finantialsSchemas.Passivo()

#         base_date = self.date_end
#         next_year = base_date + timedelta(days=365)

#         supplier_payments = (
#             self.db.query(suppliersModels.SupplierPayments)
#             .filter(suppliersModels.SupplierPayments.vencimento > self.date_end)
#             .filter(suppliersModels.SupplierPayments.date_emit <= self.date_end)
#         )

#         pbar = tqdm(
#             total=supplier_payments.count(),
#             position=0,
#             leave=True,
#             desc='Supplier Payments',
#             unit='sp'
#         )

#         for sp in supplier_payments:
#             if not sp.vencimento or not sp.valor:
#                 pbar.update(1)
#                 continue

#             vencimento = sp.vencimento.date() if isinstance(sp.vencimento, datetime) else sp.vencimento

#             supplier = Supplier(sid=sp.supplier_id, db=self.db).get_supplier()

#             payment = supplierSchemas.Payments(
#                 numero_nota=sp.numero_nota,
#                 parcela=sp.parcela,
#                 quantidade_parcelas=sp.quantidade_parcelas,
#                 valor=sp.valor,
#                 vencimento=sp.vencimento,
#                 supplier=supplier
#             )

#             if vencimento >= next_year:
#                 passivos_nao_circulante.fornecedores += sp.valor
#                 passivos_nao_circulante.fornecedores_detail.append(payment)
#             else:
#                 passivos_circulante.fornecedores += sp.valor
#                 passivos_circulante.fornecedores_detail.append(payment)

#             pbar.update(1)

#         passivo.passivos_circulantes = passivos_circulante
#         passivo.passivos_nao_circulantes = passivos_nao_circulante

#         passivo.total_passivo_circulante = (
#             passivos_circulante.emprestimos_e_financiamentos +
#             passivos_circulante.arrendamento +
#             passivos_circulante.fornecedores +
#             passivos_circulante.outras_obrigacoes
#         )

#         passivo.total_passivo_nao_circulante = (
#             passivos_nao_circulante.emprestimos_e_financiamentos +
#             passivos_nao_circulante.arrendamento +
#             passivos_nao_circulante.fornecedores +
#             passivos_nao_circulante.outras_obrigacoes
#         )

#         passivo.total_passivo = (
#             passivo.total_passivo_circulante +
#             passivo.total_passivo_nao_circulante
#         )

#         self.passivo = passivo


#     def _load_patrimonio(self):
#         details = finantialsSchemas.PatrimonioLiquidoDetalhado()
#         patrimonio_liquido = finantialsSchemas.PatrimonioLiquido()


#         patrimonio_liquido.patrimonio_liquido = 0
#         patrimonio_liquido.detalhes = details

#         self.patrimonio_liquido = patrimonio_liquido


#     def get_balance(self, show_details=False):
#         if not self.balance:
#             self._load_ativos()
#             self._load_passivos()
#             self._load_patrimonio()
        
#         if not show_details:
#             self.ativo.ativos_circulantes.detalhamento_estoque = None
#             self.passivo.passivos_circulantes.fornecedores_detail = None

#         self.balance = finantialsSchemas.BalancoPatrimonial(
#             ativo=self.ativo,
#             passivo=self.passivo,
#             patrimonio_liquido=self.patrimonio_liquido
#         )

#         return self.balance




class PatrimonialBalance:
    def __init__(
        self,
        company_id: int,
        date_begin: date,
        date_end: date,
        db: Session = Depends(get_db)
    ):
        self.company_id = company_id
        self.db = db

        self.company = Company(company_id=company_id, db=self.db).get_company()

        self.date_begin, self.date_end = normalize_period(date_begin, date_end)
        self.date_begin_dt = start_of_day(self.date_begin)
        self.date_end_dt = end_of_day(self.date_end)

        self.balance = None
        self.company = Company(company_id=company_id, db=db).get_company()
        self.ativo_circulante = finantialsSchemas.AtivoCirculante()
        self.ativos_nao_circulantes = finantialsSchemas.AtivoNaoCirculante()
        self.ativo = finantialsSchemas.Ativo()

        self.passivos_circulante = finantialsSchemas.PassivoCirculante()
        self.passivos_nao_circulante = finantialsSchemas.PassivoNaoCirculante()
        self.passivo = finantialsSchemas.Passivo()

        self.patrimonio = finantialsSchemas.PatrimonioLiquido()
        self.patrimonio_details = finantialsSchemas.PatrimonioLiquidoDetalhado()

    
    def _load_products(self):
        products = self.db.query(productModels.Product).filter(productModels.Product.company_id == self.company_id).all()
        pbar = tqdm(total=len(products), position=0, leave=True, desc='Products', unit='prod')
        for p in products:
            product = Product(pid=p.id, db=self.db).get_product_date(date=self.date_end_dt)
            self.ativo_circulante.detalhamento_estoque.append(product)
            self.ativo_circulante.estoque += product.stock_value
            pbar.update(1)


    def _load_ativos(self):
        self._load_products()


        categories = ['estrutura']
        imobilizado_query = self.db.query(suppliersModels.Purchases).filter(suppliersModels.Purchases.purchase_date <= self.date_end)\
                            .filter(suppliersModels.Purchases.category.in_(categories)).all()
        for imo in imobilizado_query:
            if imo.unit_value < 1200:
                continue
            self.ativos_nao_circulantes.imobilizado += imo.total_value
            self.ativos_nao_circulantes.imobilizado_detail.append(
                finantialsSchemas.ImobilizadoDetail(
                    item=imo.asset_name,
                    value=imo.total_value
                )
            )

        self.ativo.ativos_circulantes = self.ativo_circulante
        self.ativo.ativos_nao_circulantes = self.ativos_nao_circulantes

        self.ativo.total_ativo_circulante = self.ativo_circulante.estoque + self.ativo_circulante.caixa + self.ativo_circulante.aplicacoes + self.ativo_circulante.contas_a_receber + self.ativo_circulante.impostos_a_recuperar + self.ativo_circulante.outros_creditos
        self.ativo.total_ativo_nao_circulante = self.ativos_nao_circulantes.aplicacoes_financeiras + self.ativos_nao_circulantes.contas_a_receber + self.ativos_nao_circulantes.impostos_a_recuperar + self.ativos_nao_circulantes.outros_creditos + self.ativos_nao_circulantes.imobilizado + self.ativos_nao_circulantes.intangivel

        self.ativo.total_ativo = self.ativo.total_ativo_circulante + self.ativo.total_ativo_nao_circulante


    def _load_passivos(self):
        base_date = self.date_end
        next_year = base_date + timedelta(days=365)

        supplier_payments = (
            self.db.query(suppliersModels.SupplierPayments)
            .filter(suppliersModels.SupplierPayments.vencimento > self.date_end)
            .filter(suppliersModels.SupplierPayments.date_emit <= self.date_end)
        )

        pbar = tqdm(
            total=supplier_payments.count(),
            position=0,
            leave=True,
            desc='Supplier Payments',
            unit='sp'
        )

        for sp in supplier_payments:
            if not sp.vencimento or not sp.valor:
                pbar.update(1)
                continue

            vencimento = sp.vencimento.date() if isinstance(sp.vencimento, datetime) else sp.vencimento

            supplier = Supplier(sid=sp.supplier_id, db=self.db).get_supplier()

            payment = supplierSchemas.Payments(
                numero_nota=sp.numero_nota,
                parcela=sp.parcela,
                quantidade_parcelas=sp.quantidade_parcelas,
                valor=sp.valor,
                vencimento=sp.vencimento,
                supplier=supplier
            )

            if vencimento >= next_year:
                self.passivos_nao_circulante.fornecedores += sp.valor
                self.passivos_nao_circulante.fornecedores_detail.append(payment)
            else:
                self.passivos_circulante.fornecedores += sp.valor
                self.passivos_circulante.fornecedores_detail.append(payment)

            pbar.update(1)

        self.passivo.passivos_circulantes = self.passivos_circulante
        self.passivo.passivos_nao_circulantes = self.passivos_nao_circulante

        self.passivo.total_passivo_circulante = (
            self.passivos_circulante.emprestimos_e_financiamentos +
            self.passivos_circulante.arrendamento +
            self.passivos_circulante.fornecedores +
            self.passivos_circulante.outras_obrigacoes
        )

        self.passivo.total_passivo_nao_circulante = (
            self.passivos_nao_circulante.emprestimos_e_financiamentos +
            self.passivos_nao_circulante.arrendamento +
            self.passivos_nao_circulante.fornecedores +
            self.passivos_nao_circulante.outras_obrigacoes
        )

        self.passivo.total_passivo = (
            self.passivo.total_passivo_circulante +
            self.passivo.total_passivo_nao_circulante
        )



    def _load_patrimonio(self):
        self.patrimonio.patrimonio_liquido = 0
        self.patrimonio_details.capital_social = self.company.capital_social

        self.patrimonio.detalhes = self.patrimonio_details



    def get_balance(self, show_details=False):
        if not self.balance:
            self._load_ativos()
            # self._load_passivos()
            # self._load_patrimonio()
        
        if not show_details:
            self.ativo.ativos_circulantes.detalhamento_estoque = None
            # self.passivo.passivos_circulantes.fornecedores_detail = None

        self.balance = finantialsSchemas.BalancoPatrimonial(
            ativo=self.ativo,
            passivo=self.passivo,
            patrimonio_liquido=self.patrimonio
        )

        return self.balance

        
class Dre:
    def __init__(
        self,
        company_id: int,
        date_begin: date,
        date_end: date,
        db: Session = Depends(get_db)
    ):
        self.company_id = company_id
        self.db = db

        self.date_begin, self.date_end = normalize_period(date_begin, date_end)
        self.date_begin_dt = start_of_day(self.date_begin)
        self.date_end_dt = end_of_day(self.date_end)

        self.dre = None
        self.company = Company(company_id=company_id, db=db).get_company()

        self.total_faturamento = 0
        self.receita = finantialsSchemas.ReceitaOperacionalBruta()
        self.total_deducoes = 0
        self.deducoes = finantialsSchemas.DeducoesDeVenda()
        self.total_variaveis = 0
        self.variaveis = finantialsSchemas.GastosVariaveis()
        self.fixos = finantialsSchemas.CustosFixos()
        self.total_fixos = 0
        self.investimentos = finantialsSchemas.Investimentos()
        self.total_investimentos = 0

        self.final_balance = PatrimonialBalance(
            company_id=self.company_id,
            date_begin=self.date_begin,
            date_end=self.date_end,
            db=self.db
        )
        self.final_balance._load_ativos()
        self.final_stock = self.final_balance.ativo_circulante.estoque

        initial_stock_date = self.date_begin - timedelta(days=1)

        self.initial_balance = PatrimonialBalance(
            company_id=self.company_id,
            date_begin=initial_stock_date,
            date_end=initial_stock_date,
            db=self.db
        )
        self.initial_balance._load_ativos()
        self.initial_stock = self.initial_balance.ativo_circulante.estoque

        self.cmv_detail = finantialsSchemas.cmv_detail()



    
    def _convert_month(self):
        begin_date = date(self.year, self.month, 1)
        last_day = monthrange(self.year, self.month)[1]
        end_date = date(self.year, self.month, last_day) + timedelta(days=1) - timedelta(seconds=1)

        return begin_date, end_date
    

    def _load_receita(self):

        url = f"{API_URL}/invoices"
        params = {
            "cnpj": self.company.cnpj,
            "emit": False,
            "date_begin": self.date_begin,
            "date_end": self.date_end
        }
        req = requests.get(url=url, params=params)
        if req.status_code == 200:
            data = req.json()
            pbar = tqdm(total=len(data['invoices']), position=0, leave=True, desc='Compras', unit='nf')
            for item in data['invoices']:
                invoice = finantialsSchemas.InvoiceBase.model_validate(item)
                self.cmv_detail.compras += invoice.v_nf
                pbar.update(1)

        params = {
            "cnpj": self.company.cnpj,
            "emit": True,
            "date_begin": self.date_begin,
            "date_end": self.date_end
        }
        req = requests.get(url=url, params=params)
        if req.status_code == 200:
            data = req.json()
            pbar = tqdm(total=len(data['invoices']), position=0, leave=True, desc='Vendas', unit='nf')
            for item in data['invoices']:
                invoice = finantialsSchemas.InvoiceBase.model_validate(item)
                self.receita.vendas += invoice.v_prod
                pbar.update(1)


        self.cmv_detail.estoque_passado = self.initial_stock
        self.cmv_detail.estoque_atual = self.final_stock

        self.deducoes.custo_mercadoria_vendida = self.cmv_detail.estoque_passado + self.cmv_detail.compras - self.cmv_detail.estoque_atual
        self.deducoes.cmv_details = self.cmv_detail
        
        self._get_taxes()
        self._get_mercado_livre_infos()

        for item in self.receita:
            _, v = item
            self.total_faturamento += v

        for item in self.deducoes:
            _, v = item
            if isinstance(v, list) or isinstance(v, finantialsSchemas.cmv_detail):
                continue
            self.total_deducoes += v

    def _get_taxes(self):
        query = self.db.query(finantialsModels.Taxes).filter(finantialsModels.Taxes.company_id == self.company_id)\
                .filter(finantialsModels.Taxes.reference <= self.date_end)\
                .filter(finantialsModels.Taxes.reference >= self.date_begin).all()

        for t in query:
            if t.taxes_name == 'icms':
                self.deducoes.icms += t.value
            elif t.taxes_name == 'pis':
                self.deducoes.pis += t.value
            elif t.taxes_name == 'cofins':
                self.deducoes.cofins += t.value
            elif t.taxes_name == 'difal':
                self.deducoes.difal += t.value
            elif t.taxes_name == 'irrf':
                self.deducoes.irrf += t.value

    def _get_mercado_livre_infos(self):
        url = f'{API_URL}/mercado-livre/client/billing'
        params = {
            "company_id": self.company_id,
            # "date_begin": '2026-02-18',
            # "date_end": '2026-03-17'
            "date_begin": self.date_begin,
            "date_end": self.date_end
        }
        print(params)
        req = requests.get(url=url, params=params)
        nada = [
            'Taxa de parcelamento (equivalente ao acréscimo no preço pago pelo comprador)',
        ]
        tarifas = [
            'Custo por cobrar no Mercado Pago',
            'Taxa de parcelamento',
            'Custo por vender no Mercado Livre',
            'Tarifa de venda',
            'Tarifa de manutenção da Minha página',
            'Estorno da tarifa de venda',
            'Tarifa de devolução',
            'Custo por retirada de estoque Full',
            'Tarifa por estoque antigo no Full',
            'Tarifa pelo serviço de armazenamento Full',
            'Custo por inconformidade no Envios Full',
            'Custo do serviço de coleta Full',
            'Custo de gestão da venda',
            'Cancelamento do Custo por vender no Mercado Livre',
            'Cancelamento do Custo por cobrar no Mercado Pago',
            'Cancelamento do Taxa de parcelamento',
            'Cancelamento da tarifa por devolução',
            'Cancelamento da tarifa por campanha de publicidade - Product Ads',
        ]
        fretes = [
            'Tarifa de envio extra ou intermunicipal',
            'Tarifa por envio interno ao município',
            'Tarifa de devolução por envio interno no município',
            'Tarifa de devolução por envio externo ou intermunicipal'
            'Tarifa de devolução por envio externo ou intermunicipal'
            # 'Cancelamento da Taxa de parcelamento (equivalente ao acréscimo no preço pago pelo comprador)',
            # 'Cancelamento da tarifa por envio interno ao município',
            # 'Cancelamento da tarifa de envio extra ou intermunicipal',
            # 'Cancelamento da tarifa de devolução por envio interno no município'
            # 'Cancelamento da tarifa de devolução por envio externo ou intermunicipal'
        ]
        publicidade = [
            'Tarifa por campanha de publicidade - Product Ads',
            'Tarifa por campanha de publicidade - Display Ads',
            'Cancelamento da tarifa por campanha de publicidade - Product Ads',
            'Anulación del cargo por campaña de publicidad - Display'
        ]
        comissoes = [
            'Tarifa de venda com afiliados'
        ]
        difal = [
            'Cobrança do diferencial de alíquota interestadual (ICMS-DIFAL)'
        ]


        costs = {}
        if req.status_code == 200:
            data = req.json()
            print(len(data))
            for item in data:
                bill = finantialsSchemas.MercadoLivreBillingItem.model_validate(item)
                if bill.detalhe not in costs:
                    costs[bill.detalhe] = bill.valor
                else:
                    costs[bill.detalhe] += bill.valor
                if bill.detalhe in nada:
                    continue
                elif bill.detalhe in tarifas:
                    self.deducoes.tarifas += bill.valor
                elif bill.detalhe in fretes:
                    if not bill.envio_cliente:
                        bill.envio_cliente = 0
                    self.deducoes.frete += (bill.valor - bill.envio_cliente)
                elif bill.detalhe in publicidade:
                    self.investimentos.publicidade += bill.valor
                elif bill.detalhe in comissoes:
                    self.deducoes.comissoes += bill.valor
                elif bill.detalhe in difal:
                    self.deducoes.difal += bill.valor

            # print(costs)
        self._get_tm_costs()
        self._get_shopee_tariffs()

    def _get_variaveis(self):
        gastos = ['insumo']
        gastos_query = self.db.query(suppliersModels.Purchases)\
                        .filter(suppliersModels.Purchases.purchase_date >= self.date_begin)\
                        .filter(suppliersModels.Purchases.purchase_date <= self.date_end)\
                        .filter(suppliersModels.Purchases.category.in_(gastos)).all()
        self.variaveis.insumos = sum([g.total_value for g in gastos_query])
        self.total_variaveis = 0
        for item in self.variaveis:
            _, v = item
            self.total_variaveis += v

    def _get_custos_fixos(self):
        employee_payments = (
            self.db.query(accountModels.EmployeePayroll)
            .filter(accountModels.EmployeePayroll.data_competencia >= self.date_begin)
            .filter(accountModels.EmployeePayroll.data_competencia <= self.date_end)
            .all()
        )

        for ep in employee_payments:
            employee = Employee(emp_id=ep.employee_id, db=self.db).get_employee()

            if employee.position == 'Sócio Administrativo':
                self.fixos.pro_labore += ep.salario_liquido
            else:
                self.fixos.folha_salarial += ep.salario_liquido

        custos_fixos = (
            self.db.query(finantialsModels.Fixos)
            .filter(finantialsModels.Fixos.company_id == self.company_id)
            .filter(finantialsModels.Fixos.payment_date >= self.date_begin)
            .filter(finantialsModels.Fixos.payment_date <= self.date_end)
            .all()
        )

        for item in custos_fixos:
            if item.name == 'software':
                self.fixos.software += item.value
            elif item.name == 'aluguel':
                self.fixos.aluguel += item.value
            elif item.name == 'contabilidade':
                self.fixos.contabilidade += item.value
            elif item.name == 'internet':
                self.fixos.internet += item.value
            elif item.name == 'luz':
                self.fixos.luz += item.value
            elif item.name == 'agua':
                self.fixos.agua += item.value

        for _, v in self.fixos:
            self.total_fixos += v

    def _get_investimentos(self):
        self.total_investimentos = self.investimentos.publicidade

    def _get_tm_costs(self):
        url = f'{API_URL}/freight'
        params = {
            "company_id": self.company_id,
            "date_begin": self.date_begin,
            "date_end": self.date_end
        }
        req = requests.get(url=url, params=params)
        if req.status_code == 200:
            data = req.json()            
            for item in data:
                f_costs = finantialsSchemas.FreightCostsTM.model_validate(item)
                self.deducoes.frete += f_costs.valor

    def _get_shopee_tariffs(self):
        url = f'{API_URL}/shopee/taxes'
        params = {
            "company_id": self.company_id,
            "date_begin": self.date_begin,
            "date_end": self.date_end
        }
        req = requests.get(url=url, params=params)
        if req.status_code == 200:
            data = req.json()            
            for item in data:
                t_costs = finantialsSchemas.ShopeeTariffs.model_validate(item)
                if 'Inserção da Campanha de Afiliados do Vendedor' in t_costs.descricao:
                    self.deducoes.comissoes += t_costs.valor
                elif 'Inserção de propaganda e publicidade' in t_costs.descricao:
                    self.investimentos.publicidade += t_costs.valor
                elif 'Serviços prestados de comissão Shopee Antecipa' in t_costs.descricao:
                    self.deducoes.tarifas += t_costs.valor
                elif 'Serviços prestados de comissão' in t_costs.descricao:
                    self.deducoes.tarifas += t_costs.valor
                elif 'Serviços opcionais/personalizados prestados' in t_costs.descricao:
                    self.deducoes.tarifas += t_costs.valor
                elif 'Abatimento' in t_costs.descricao:
                    self.deducoes.tarifas += t_costs.valor
                elif 'Serviço de processamento de pagamentos' in t_costs.descricao:
                    self.deducoes.tarifas += t_costs.valor
                


    def get_dre(self, show_details=False):
        if not self.dre:
            self._load_receita()
            self._get_variaveis()
            self._get_custos_fixos()
            self._get_investimentos()
        
        if not show_details:
            self.deducoes.custo_mercadoria_vendida_details = None

        self.dre = finantialsSchemas.DRE(
            faturamento=self.total_faturamento,
            receita_operacional_bruta=self.receita,
            total_deducoes_de_venda=self.total_deducoes,
            deducoes_de_venda=self.deducoes,
            receita_liquida_de_vendas=self.total_faturamento - self.total_deducoes,
            total_gastos_variaveis=self.total_variaveis,
            gastos_variaveis=self.variaveis
        )
        self.dre.lucro_bruto = self.dre.receita_liquida_de_vendas - self.dre.total_gastos_variaveis
        self.dre.total_custos_fixos = self.total_fixos
        self.dre.custos_fixos = self.fixos
        self.dre.lucro_operacional = self.dre.lucro_bruto - self.dre.total_custos_fixos
        self.dre.total_investimentos = self.total_investimentos
        self.dre.investimentos = self.investimentos

        return self.dre


class MultipleDRE:
    def __init__(
        self,
        months: List[int],
        year: int,
        company_id: int,
        db: Session = Depends(get_db)
    ):
        self.db = db
        self.year = year
        self.company_id = company_id

        if not months:
            raise ValueError("Informe ao menos um mês.")

        invalid_months = [m for m in months if m < 1 or m > 12]
        if invalid_months:
            raise ValueError(f"Meses inválidos: {invalid_months}. Use meses de 1 a 12.")

        self.months = sorted(list(set(months)))

        self.dres = [
            Dre(
                company_id=self.company_id,
                month=month,
                year=self.year,
                db=self.db
            ).get_dre(show_details=True)
            for month in self.months
        ]

        self.company = Company(company_id=company_id, db=db).get_company()

        self.dre = None

    def _months_are_consecutive(self):
        return self.months == list(range(self.months[0], self.months[-1] + 1))

    def _sum_schema(self, schema_class, attr: str):
        result = schema_class()

        for dre in self.dres:
            schema_obj = getattr(dre, attr, None)

            if not schema_obj:
                continue

            for field_name, value in schema_obj:
                if isinstance(value, (int, float)):
                    current_value = getattr(result, field_name, 0) or 0
                    setattr(result, field_name, current_value + value)

        return result

    def _sum_numeric_fields(self, schema_obj):
        total = 0

        for _, value in schema_obj:
            if isinstance(value, (int, float)):
                total += value

        return total

    def _build_cmv_detail(self):
        cmv_detail = finantialsSchemas.cmv_detail()

        cmv_details = [
            dre.deducoes_de_venda.cmv_details
            for dre in self.dres
            if dre.deducoes_de_venda and dre.deducoes_de_venda.cmv_details
        ]

        if not cmv_details:
            return cmv_detail

        cmv_detail.estoque_passado = cmv_details[0].estoque_passado
        cmv_detail.estoque_atual = cmv_details[-1].estoque_atual
        cmv_detail.compras = sum(cmv.compras for cmv in cmv_details)

        return cmv_detail

    def _get_cmv_value(self, cmv_detail):
        if self._months_are_consecutive():
            return (
                cmv_detail.estoque_passado +
                cmv_detail.compras -
                cmv_detail.estoque_atual
            )

        return sum(
            dre.deducoes_de_venda.custo_mercadoria_vendida or 0
            for dre in self.dres
        )

    def get_dre(self, show_details=False):
        receita = self._sum_schema(
            finantialsSchemas.ReceitaOperacionalBruta,
            "receita_operacional_bruta"
        )

        deducoes = self._sum_schema(
            finantialsSchemas.DeducoesDeVenda,
            "deducoes_de_venda"
        )

        gastos_variaveis = self._sum_schema(
            finantialsSchemas.GastosVariaveis,
            "gastos_variaveis"
        )

        custos_fixos = self._sum_schema(
            finantialsSchemas.CustosFixos,
            "custos_fixos"
        )

        investimentos = self._sum_schema(
            finantialsSchemas.Investimentos,
            "investimentos"
        )

        cmv_detail = self._build_cmv_detail()

        deducoes.custo_mercadoria_vendida = self._get_cmv_value(cmv_detail)

        if show_details:
            deducoes.cmv_details = cmv_detail
        else:
            deducoes.cmv_details = None

        total_faturamento = self._sum_numeric_fields(receita)
        total_deducoes = self._sum_numeric_fields(deducoes)
        total_gastos_variaveis = self._sum_numeric_fields(gastos_variaveis)
        total_custos_fixos = self._sum_numeric_fields(custos_fixos)
        total_investimentos = self._sum_numeric_fields(investimentos)

        self.dre = finantialsSchemas.DRE(
            faturamento=total_faturamento,
            receita_operacional_bruta=receita,
            total_deducoes_de_venda=total_deducoes,
            deducoes_de_venda=deducoes,
            receita_liquida_de_vendas=total_faturamento - total_deducoes,
            total_gastos_variaveis=total_gastos_variaveis,
            gastos_variaveis=gastos_variaveis,
        )

        self.dre.lucro_bruto = (
            self.dre.receita_liquida_de_vendas -
            self.dre.total_gastos_variaveis
        )

        self.dre.total_custos_fixos = total_custos_fixos
        self.dre.custos_fixos = custos_fixos

        self.dre.lucro_operacional = (
            self.dre.lucro_bruto -
            self.dre.total_custos_fixos
        )

        self.dre.total_investimentos = total_investimentos
        self.dre.investimentos = investimentos

        return self.dre


class CashFlow:
    pass


