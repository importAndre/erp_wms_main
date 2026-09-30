"""Revisão da classe Dre.

INTEGRAÇÃO OBRIGATÓRIA: a rota deve retornar DreResultado (contrato v2).
MultipleDRE permanece no contrato antigo e NÃO é compatível com a nova Dre.
Não usar o consolidado até migrar seu agregador e schema.
Detalhes e limites de competência estão documentados na classe Dre.
"""
from decimal import Decimal, ROUND_HALF_UP
from copy import deepcopy
from pydantic import BaseModel

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
from typing import Union, Optional, List
from sqlalchemy import func, case
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


historical_products = {}

class PatrimonialBalance:
    def __init__(
        self,
        company_id: int,
        date_begin: date,
        date_end: Optional[datetime] = None,
        db: Session = Depends(get_db)
    ):
        self.company_id = company_id
        self.db = db

        self.company = Company(company_id=company_id, db=self.db).get_company()

        self.date_begin, self.date_end = normalize_period(date_begin, date_end)
        self.date_begin_dt = start_of_day(self.date_begin)
        if date_end:
            self.date_end_dt = end_of_day(self.date_end)
        else:
            self.date_end_dt = None


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
        global historical_products
        if self.date_end_dt in historical_products:
            self.ativo_circulante.detalhamento_estoque = historical_products[self.date_end_dt]
            for item in historical_products[str(self.date_begin_dt)]:
                self.ativo_circulante.estoque += item.stock_value
            return


        products = self.db.query(productModels.Product).filter(productModels.Product.company_id == self.company_id).all()
        pbar = tqdm(total=len(products), position=0, leave=True, desc='Products', unit='prod')
        for p in products:
            if self.date_begin_dt:
                # print(self.date_begin_dt, self.date_end_dt)
                product = Product(pid=p.id, db=self.db).get_product_date(date=self.date_end_dt)
                # if p.sku == '6.ESTIL.PROF.25':
                #     print(p.sku, p.available_stock, p.virtual_stock)
                #     print(product.sku, product.available_stock, product.virtual_stock)
            else:
                product = Product(pid=p.id, db=self.db).get_product()

            self.ativo_circulante.detalhamento_estoque.append(product)
            self.ativo_circulante.estoque += product.stock_value
            
            pbar.update(1)
        historical_products[str(self.date_end_dt)] = self.ativo_circulante.detalhamento_estoque

    def _load_transactions(self):
        filter_params = [
            finantialsModels.Transactions.transaction_date >= self.date_begin_dt,
            finantialsModels.Transactions.company_id == self.company_id
        ]

        if self.date_end_dt:
            filter_params.append(
                finantialsModels.Transactions.transaction_date <= self.date_end_dt
            )

        total = (
            self.db.query(
                func.coalesce(
                    func.sum(
                        case(
                            (
                                finantialsModels.Transactions.method == True,
                                finantialsModels.Transactions.value
                            ),
                            else_=finantialsModels.Transactions.value * -1
                        )
                    ),
                    0
                )
            )
            .filter(*filter_params)
            .scalar()
        )

        self.ativo_circulante.caixa = total


    def _load_ativos(self):
        self._load_products()
        self._load_transactions()


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
    """DRE gerencial com grupos separados e importação sem falhas silenciosas.

    Integração:
      * Substitui apenas Dre; PatrimonialBalance e CashFlow não são alterados.
      * A rota deve usar response_model=DreResultado, não finantialsSchemas.DRE.
      * MultipleDRE antigo precisa migrar para este contrato antes de ser usado.
      * Queries exigem company_id no modelo. Se o vínculo for indireto, faça
        o JOIN em _query_company; nunca retire o filtro de empresa.

    Contratos opcionais para uma apuração validada:
      normalizar_nota(item, emit) -> None (excluir) ou dict de valores assinados:
        emit=True: vendas, devolucoes, descontos_incondicionais;
        emit=False: compras (custo de revenda líquido de tributos recuperáveis).
        O adaptador deve filtrar canceladas/remessas/transferências e tratar
        devoluções, frete e descontos conforme a natureza fiscal, sem dupla conta.
      calcular_folha(ep) -> dict: folha_salarial, pro_labore, encargos, beneficios,
        provisoes (despesa por competência, sem dupla conta de retenções).

    Os endpoints devem entregar TODAS as linhas do intervalo, sem paginação
    escondida, no mesmo fuso do banco. Valores são débitos positivos / créditos
    negativos; cancelamentos textuais são normalizados para negativos.
    As fontes alternativas são exclusivas para evitar dupla contagem. Essa
    escolha não é conciliação automática: cobertura e competência precisam ser
    verificadas antes de ativar fontes_validadas=True.
    """

    _ZERO = Decimal('0')
    _CENT = Decimal('0.01')

    def __init__(self, company_id: int, date_begin: date, date_end: date,
                 db: Session = Depends(get_db), *,
                 fonte_publicidade='marketplaces', fonte_difal='tributos',
                 irrf_tratamento='pendente', normalizar_nota=None,
                 calcular_folha=None, fontes_validadas=False,
                 tributos_lucro_apurados=False, timeout=30):
        self.company_id = company_id
        self.db = db
        self.date_begin, self.date_end = normalize_period(date_begin, date_end)
        self.date_begin_dt = start_of_day(self.date_begin)
        self.date_end_dt = end_of_day(self.date_end)
        if fonte_publicidade not in {'marketplaces', 'transacoes'}:
            raise ValueError('fonte_publicidade: marketplaces ou transacoes.')
        if fonte_difal not in {'tributos', 'marketplace'}:
            raise ValueError('fonte_difal: tributos ou marketplace.')
        if irrf_tratamento not in {'pendente', 'recuperavel', 'retencao_terceiros'}:
            raise ValueError('Classifique a natureza do IRRF antes de incluí-lo.')
        if timeout <= 0:
            raise ValueError('timeout deve ser positivo.')
        self.fonte_publicidade = fonte_publicidade
        self.fonte_difal = fonte_difal
        self.irrf_tratamento = irrf_tratamento
        self.normalizar_nota = normalizar_nota
        self.calcular_folha = calcular_folha
        self.fontes_validadas = fontes_validadas
        self.tributos_lucro_apurados = tributos_lucro_apurados
        self.timeout = timeout
        self.company = Company(company_id=company_id, db=db).get_company()
        self._loaded = False
        self.dre = None
        self._reset()

    def _reset(self):
        self.contas = {name: {} for name in (
            'receita', 'deducoes', 'variaveis', 'fixos', 'financeiras_receitas',
            'financeiras_despesas', 'tributos_lucro', 'fora')}
        self.compras = self._ZERO
        self.initial_stock = self._ZERO
        self.final_stock = self._ZERO
        self.avisos = []
        self.pendencias = []
        self.detalhes = {name: [] for name in ('notas', 'tributos', 'marketplaces')}
        if not self.fontes_validadas:
            self._warn('Apuração provisória: validar competência, completude dos '
                       'endpoints, natureza das notas, créditos tributários, estoque, '
                       'encargos/provisões/depreciação e sobreposição entre fontes. '
                       'Valores em Taxes podem ser impostos a pagar líquidos de '
                       'créditos, não necessariamente despesa tributária de vendas.')

    @classmethod
    def _decimal(cls, value):
        if value is None or isinstance(value, bool):
            raise ValueError('Valor monetário ausente ou inválido.')
        result = Decimal(str(value))
        if not result.is_finite():
            raise ValueError('Valor monetário não finito.')
        return result

    @classmethod
    def _money(cls, value):
        return cls._decimal(value).quantize(cls._CENT, rounding=ROUND_HALF_UP)

    def _add(self, group, field, value):
        target = self.contas[group]
        target[field] = target.get(field, self._ZERO) + self._decimal(value)

    def _warn(self, message):
        if message not in self.avisos:
            self.avisos.append(message)

    def _pending(self, source, description, value):
        self.pendencias.append({'fonte': source, 'descricao': description,
                                'valor': self._money(value)})

    def _query_company(self, model):
        if not hasattr(model, 'company_id'):
            raise ValueError(
                f'{model.__name__} não expõe company_id. Adapte _query_company '
                'com JOIN pelo vínculo real da empresa; não faça consulta global.')
        return self.db.query(model).filter(model.company_id == self.company_id)

    def _period_query(self, model, field):
        column = getattr(model, field)
        # SQL Date usa date; DateTime usa datetime, incluindo o último dia.
        try:
            is_date = column.type.python_type is date
        except (AttributeError, NotImplementedError):
            raise ValueError(f'Não foi possível determinar o tipo de {field}.')
        begin = self.date_begin if is_date else self.date_begin_dt
        end = self.date_end if is_date else self.date_end_dt
        return self._query_company(model).filter(column >= begin, column <= end)

    def _get_json(self, path, params, *, key=None):
        response = requests.get(f'{API_URL}{path}', params=params, timeout=self.timeout)
        response.raise_for_status()
        payload = response.json()
        if key is not None:
            if not isinstance(payload, dict) or key not in payload:
                raise ValueError(f'Resposta inválida de {path}: falta {key}.')
            payload = payload[key]
        if not isinstance(payload, list):
            raise ValueError(f'Resposta inválida de {path}: esperado array completo.')
        return payload

    def _params(self):
        return {'company_id': self.company_id, 'date_begin': self.date_begin,
                'date_end': self.date_end}

    def _stock_at(self, when):
        # Não usa o cache global defeituoso de PatrimonialBalance. Estoque fica
        # isolado por empresa e requisição; a avaliação histórica ainda depende
        # da correção de Product.get_product_date no projeto.
        total = self._ZERO
        for row in self._query_company(productModels.Product).all():
            product = Product(pid=row.id, db=self.db).get_product_date(date=when)
            if product is None:
                raise ValueError(f'Estoque histórico indisponível: produto {row.id}.')
            total += self._decimal(product.stock_value)
        return total

    def _load_receita(self):
        self.initial_stock = self._stock_at(
            end_of_day(self.date_begin - timedelta(days=1)))
        self.final_stock = self._stock_at(self.date_end_dt)
        if self.normalizar_nota is None:
            self._warn('CMV/vendas provisórios: notas usam v_nf/v_prod legados. '
                       'Forneça normalizar_nota para custo líquido de revenda, '
                       'cancelamentos, devoluções, descontos e natureza fiscal.')
        for emit in (False, True):
            params = {'cnpj': self.company.cnpj, 'emit': emit,
                      'date_begin': self.date_begin, 'date_end': self.date_end}
            for item in self._get_json('/invoices', params, key='invoices'):
                if self.normalizar_nota:
                    values = self.normalizar_nota(item, emit)
                else:
                    invoice = finantialsSchemas.InvoiceBase.model_validate(item)
                    values = ({'vendas': invoice.v_prod} if emit
                              else {'compras': invoice.v_nf})
                if values is None:
                    continue
                allowed = ({'vendas', 'devolucoes', 'descontos_incondicionais'}
                           if emit else {'compras'})
                if not isinstance(values, dict) or not values or set(values) - allowed:
                    raise ValueError('normalizar_nota retornou contas inválidas.')
                for field, value in values.items():
                    if field == 'compras':
                        self.compras += self._decimal(value)
                    else:
                        self._add('receita' if field == 'vendas' else 'deducoes', field, value)
                self.detalhes['notas'].append({'emit': emit, 'valores': values})

    def _get_taxes(self):
        mapping = {'ICMS': ('deducoes', 'icms'),
                   'PIS/COFINS': ('deducoes', 'pis_cofins'),
                   'PIS': ('deducoes', 'pis'), 'COFINS': ('deducoes', 'cofins'),
                   'IOF': ('financeiras_despesas', 'iof'),
                   'IRPJ': ('tributos_lucro', 'irpj'),
                   'CSLL': ('tributos_lucro', 'csll')}
        for row in self._period_query(finantialsModels.Taxes, 'reference').all():
            name = row.taxes_name.strip().upper()
            value = self._decimal(row.value)
            self.detalhes['tributos'].append({'nome': name, 'valor': value})
            if name == 'DIFAL':
                if self.fonte_difal == 'tributos':
                    self._add('deducoes', 'difal', value)
            elif name == 'IRRF':
                self._add('fora', 'irrf_' + self.irrf_tratamento, value)
                if self.irrf_tratamento == 'pendente':
                    self._pending('Taxes', 'IRRF: confirmar recuperável ou retenção de terceiros', value)
            elif name in mapping:
                self._add(*mapping[name], value)
            else:
                self._pending('Taxes', name, value)
        taxes = self.contas['deducoes']
        if 'pis_cofins' in taxes and ('pis' in taxes or 'cofins' in taxes):
            self._warn('PIS/COFINS conjunto e separado no período: verificar duplicidade.')

    @classmethod
    def _signed_bill(cls, description, value):
        amount = cls._decimal(value)
        text = description.casefold()
        if text.startswith(('cancelamento', 'estorno', 'anulación', 'abatimento')):
            return -abs(amount)
        return amount

    def _get_mercado_livre_infos(self):
        tariffs = {
            'Custo por cobrar no Mercado Pago', 'Taxa de parcelamento',
            'Custo por vender no Mercado Livre', 'Tarifa de venda',
            'Tarifa de manutenção da Minha página', 'Estorno da tarifa de venda',
            'Tarifa de devolução', 'Custo por retirada de estoque Full',
            'Tarifa por estoque antigo no Full', 'Tarifa pelo serviço de armazenamento Full',
            'Custo por inconformidade no Envios Full', 'Custo do serviço de coleta Full',
            'Custo de gestão da venda', 'Cancelamento do Custo por vender no Mercado Livre',
            'Cancelamento do Custo por cobrar no Mercado Pago',
            'Cancelamento do Taxa de parcelamento', 'Cancelamento da tarifa por devolução',
        }
        freight = {
            'Tarifa de envio extra ou intermunicipal', 'Tarifa por envio interno ao município',
            'Tarifa de devolução por envio interno no município',
            'Tarifa de devolução por envio externo ou intermunicipal',
        }
        freight |= {'Cancelamento da ' + name[0].lower() + name[1:]
                    for name in tuple(freight)}
        ads = {'Tarifa por campanha de publicidade - Product Ads',
               'Tarifa por campanha de publicidade - Display Ads',
               'Cancelamento da tarifa por campanha de publicidade - Product Ads',
               'Cancelamento da tarifa por campanha de publicidade - Display Ads',
               'Anulación del cargo por campaña de publicidad - Display'}
        ignored = {'Taxa de parcelamento (equivalente ao acréscimo no preço pago pelo comprador)',
                   'Cancelamento da Taxa de parcelamento (equivalente ao acréscimo no preço pago pelo comprador)'}
        for item in self._get_json('/mercado-livre/client/billing', self._params()):
            bill = finantialsSchemas.MercadoLivreBillingItem.model_validate(item)
            name = bill.detalhe.strip()
            value = self._signed_bill(name, bill.valor)
            self.detalhes['marketplaces'].append({'fonte': 'ML', 'descricao': name, 'valor': value})
            if name in ignored:
                continue
            if name in ads:
                if self.fonte_publicidade == 'marketplaces':
                    self._add('variaveis', 'publicidade', value)
            elif name in tariffs:
                self._add('variaveis', 'tarifas', value)
            elif name in freight:
                customer = self._signed_bill(name, bill.envio_cliente or 0)
                self._add('variaveis', 'frete', value - customer)
            elif name in {'Tarifa de venda com afiliados', 'Cancelamento da tarifa de venda com afiliados'}:
                self._add('variaveis', 'comissoes', value)
            elif name == 'Cobrança do diferencial de alíquota interestadual (ICMS-DIFAL)':
                if self.fonte_difal == 'marketplace':
                    self._add('deducoes', 'difal', value)
            else:
                self._pending('Mercado Livre', name, value)
        self._get_tm_costs()
        self._get_shopee_tariffs()

    def _get_tm_costs(self):
        for item in self._get_json('/freight', self._params()):
            freight = finantialsSchemas.FreightCostsTM.model_validate(item)
            self._add('variaveis', 'frete', freight.valor)

    def _get_shopee_tariffs(self):
        for item in self._get_json('/shopee/taxes', self._params()):
            bill = finantialsSchemas.ShopeeTariffs.model_validate(item)
            name = bill.descricao.strip()
            value = self._signed_bill(name, bill.valor)
            self.detalhes['marketplaces'].append({'fonte': 'Shopee', 'descricao': name, 'valor': value})
            if 'Inserção da Campanha de Afiliados do Vendedor' in name:
                self._add('variaveis', 'comissoes', value)
            elif 'Inserção de propaganda e publicidade' in name:
                if self.fonte_publicidade == 'marketplaces':
                    self._add('variaveis', 'publicidade', value)
            elif 'Serviços prestados de comissão Shopee Antecipa' in name:
                self._add('financeiras_despesas', 'antecipacao_recebiveis', value)
            elif any(text in name for text in ('Serviços prestados de comissão',
                     'Serviços opcionais/personalizados prestados',
                     'Serviço de processamento de pagamentos')):
                self._add('variaveis', 'tarifas', value)
            else:
                # Um abatimento sem referência pode ser de anúncios ou frete.
                self._pending('Shopee', name, value)

    def _get_variaveis(self):
        query = self._period_query(suppliersModels.Purchases, 'purchase_date')
        for row in query.filter(suppliersModels.Purchases.category == 'insumo').all():
            self._add('variaveis', 'insumos', row.total_value)
        self._warn('Insumos por data de compra: confirmar consumo na competência '
                   'e exclusão dessas notas das compras destinadas ao CMV.')

    def _get_custos_fixos(self):
        payroll = self._period_query(accountModels.EmployeePayroll, 'data_competencia')
        for ep in payroll.all():
            if self.calcular_folha:
                amounts = self.calcular_folha(ep)
                allowed = {'folha_salarial', 'pro_labore', 'encargos', 'beneficios', 'provisoes'}
                if not isinstance(amounts, dict) or not amounts or set(amounts) - allowed:
                    raise ValueError('calcular_folha retornou contas inválidas.')
                for name, value in amounts.items():
                    self._add('fixos', name, value)
            else:
                employee = Employee(emp_id=ep.employee_id, db=self.db).get_employee()
                value = getattr(ep, 'salario_bruto', None)
                if value is None:
                    value = ep.salario_liquido
                    self._warn('Folha provisória: salário bruto indisponível; líquido '
                               'usado apenas como estimativa. Forneça calcular_folha.')
                key = 'pro_labore' if employee.position == 'Sócio Administrativo' else 'folha_salarial'
                self._add('fixos', key, value)
                self._warn('Folha sem validação de encargos, benefícios, férias e 13º; '
                           'forneça calcular_folha para o custo completo.')
        model = finantialsModels.Fixos
        field = next((name for name in ('data_competencia', 'reference')
                      if hasattr(model, name)), 'payment_date')
        if field == 'payment_date':
            self._warn('Custos fixos usam payment_date: falta campo de competência no modelo.')
        rows = self._period_query(model, field).all()
        if field != 'payment_date':
            # Fallback somente para registros SEM competência. Um pagamento
            # em março com competência em fevereiro não pertence a março.
            fallback_rows = self._period_query(model, 'payment_date').filter(
                getattr(model, field).is_(None)
            ).all()
            if fallback_rows:
                fallback_total = sum(
                    (self._decimal(row.value) for row in fallback_rows), self._ZERO)
                self._warn(
                    f'Custos fixos provisórios: {len(fallback_rows)} lançamento(s), '
                    f'total R$ {self._money(fallback_total)}, sem {field}; '
                    'incluídos por payment_date. Preencha a competência para '
                    'apuração definitiva. Não foi presumido o mês anterior.')
                rows.extend(fallback_rows)
        names = {'SOFTWARE': 'software', 'ALUGUEL': 'aluguel',
                 'CONTABILIDADE': 'contabilidade', 'INTERNET': 'internet',
                 'LUZ': 'luz', 'AGUA': 'agua'}
        for item in rows:
            self._add('fixos', names.get(item.name, 'outros'), item.value)

    def get_other_infos(self):
        self._warn('Transações bancárias são por data de movimentação; despesas '
                   'administrativas, financeiro e anúncios dessa fonte exigem '
                   'conciliação com a competência. Pagamento de fatura de cartão '
                   'não é uma nova despesa; importe os itens por natureza.')
        query = self._period_query(finantialsModels.Transactions, 'transaction_date')
        for item in query.all():
            if item.method not in (True, False):
                raise ValueError('Transactions.method deve indicar entrada/saída.')
            value = abs(self._decimal(item.value))
            income = bool(item.method)
            expense = -value if income else value
            if item.category in (10, 18):
                self._add('financeiras_receitas', 'rendimentos', -expense)
            elif item.category == 19:
                if self.fonte_publicidade == 'transacoes':
                    self._add('variaveis', 'publicidade', expense)
                elif value:
                    self._warn('Categoria 19 não somada: publicidade vem dos marketplaces. '
                               'Concilie anúncios externos e pagamentos já importados.')
            elif item.category == 20:
                self._add('fora', 'resgates' if income else 'aplicacoes', value)
            elif item.category == 22:
                self._add('fixos', 'despesas_administrativas', expense)
            elif item.category == 11:
                self._add('financeiras_despesas', 'despesas_bancarias', expense)
            elif item.category == 7:
                self._add('fora', 'distribuicao_lucros', expense)
            elif item.category == 6:
                self._add('fora', 'pagamento_cartao_a_conciliar', expense)
                if value:
                    self._pending('Transactions', 'Cartão: conciliar itens; pagamento não é despesa', expense)
            elif item.category == 17:
                self._add('fora', 'pagamento_emprestimo_a_conciliar', expense)
                if value:
                    self._pending('Transactions', 'Empréstimo: separar principal, juros e encargos', expense)
            elif item.category not in {1, 2, 3, 4, 5, 8, 9, 12, 13, 14, 15, 16, 21}:
                self._pending('Transactions', f'Categoria não mapeada: {item.category}', expense)

    def _load(self):
        # Uma falha pode ter ocorrido após carregar parte das fontes. Sempre
        # reinicia antes de tentar novamente, sem acumular valores da tentativa.
        self._reset()
        self._load_receita()
        self._get_taxes()
        self._get_mercado_livre_infos()
        self._get_variaveis()
        self._get_custos_fixos()
        self.get_other_infos()
        self._loaded = True

    def get_dre(self, show_details=False, desired_margin=10):
        desired = self._decimal(desired_margin) / 100
        if not self._ZERO <= desired < 1:
            raise ValueError('desired_margin deve estar entre 0 (inclusivo) e 100 (exclusivo).')
        if not self._loaded:
            self._load()
        groups = {group: {key: self._money(value) for key, value in amounts.items()}
                  for group, amounts in self.contas.items()}
        total = lambda group: sum(groups[group].values(), self._ZERO)
        revenue = total('receita')
        deductions = total('deducoes')
        net = revenue - deductions
        cmv_detail = {'estoque_passado': self._money(self.initial_stock),
                      'compras': self._money(self.compras),
                      'estoque_atual': self._money(self.final_stock)}
        cmv = cmv_detail['estoque_passado'] + cmv_detail['compras'] - cmv_detail['estoque_atual']
        gross = net - cmv
        variable = total('variaveis')
        contribution = gross - variable
        ratio = contribution / revenue if revenue > 0 else None
        fixed = total('fixos')
        operating = contribution - fixed
        financial = total('financeiras_receitas') - total('financeiras_despesas')
        before_tax = operating + financial
        warnings = list(self.avisos)
        if cmv < 0:
            warnings.append('CMV negativo: revisar estoque inicial/final e custo de aquisição.')
        if ratio is None or ratio <= 0:
            warnings.append('Ponto de equilíbrio indisponível: receita ou contribuição não positiva.')
        break_even = self._money(fixed / ratio) if ratio is not None and ratio > 0 else None
        target_even = (self._money(fixed / (ratio - desired))
                       if ratio is not None and ratio > desired else None)
        if target_even is None:
            warnings.append('Meta de margem não alcançável com a contribuição atual.')
        if not self.tributos_lucro_apurados:
            warnings.append('IRPJ/CSLL não confirmados para o período: lucro_liquido indisponível.')
        # Não transforma resultado contábil em suposto saldo de caixa. Nem
        # aplicações nem distribuições são subtraídas do lucro.
        result = finantialsSchemas.DreResultado(
            date_begin=self.date_begin, date_end=self.date_end,
            faturamento=revenue, receita_operacional_bruta=groups['receita'],
            total_deducoes_de_venda=deductions, deducoes_de_venda=groups['deducoes'],
            receita_liquida_de_vendas=net, custo_mercadoria_vendida=cmv,
            cmv_details=cmv_detail, lucro_bruto=gross,
            total_gastos_variaveis=variable, gastos_variaveis=groups['variaveis'],
            margem_contribuicao_valor=contribution, margem_contribuicao=ratio,
            total_custos_fixos=fixed, custos_fixos=groups['fixos'],
            lucro_operacional=operating, receitas_financeiras=groups['financeiras_receitas'],
            despesas_financeiras=groups['financeiras_despesas'], resultado_financeiro=financial,
            resultado_antes_irpj_csll=before_tax, tributos_sobre_lucro=groups['tributos_lucro'],
            lucro_liquido=(before_tax - total('tributos_lucro')
                           if self.tributos_lucro_apurados else None),
            fora_da_dre=groups['fora'],
            distribuicao_lucros=groups['fora'].get('distribuicao_lucros', self._ZERO),
            ponto_de_equilibrio_contabil=break_even,
            ponto_de_equilibrio_economico=target_even,
            provisorio=bool(warnings or self.pendencias), avisos=warnings,
            pendencias=deepcopy(self.pendencias),
            detalhes=deepcopy(self.detalhes) if show_details else None)
        # Retorno independente: ocultar detalhes ou alterar a resposta não
        # destrói os dados internos, nem dobra a distribuição em nova chamada.
        self.dre = result.model_copy(deep=True)
        return result


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
    def __init__(
        self,
        company_id: int,
        date_begin: date,
        date_end: date,
        future_date: Optional[date] = None,
        db: Session = Depends(get_db)
    ):
        self.company_id = company_id
        self.db = db

        self.date_begin, self.date_end = normalize_period(date_begin, date_end)
        self.date_begin_dt = start_of_day(self.date_begin)
        self.date_end_dt = end_of_day(self.date_end)

        if future_date:
            self.future_date, _ = normalize_period(future_date, future_date)
            self.future_date_dt = end_of_day(self.future_date)
        else:
            self.future_date_dt = None

        self.company = Company(company_id=company_id, db=db).get_company()

        self.entradas_operacionais = finantialsSchemas.DFCEntradasOperacionais()
        self.entradas_nao_operacionais = finantialsSchemas.DFCEntradasNaoOperacionais()
        self.entradas = finantialsSchemas.DFCEntradas()
        self.impostos = finantialsSchemas.DeducoesDeVenda()
        self.fixos = finantialsSchemas.CustosFixos()
        self.saidas_operacionais = finantialsSchemas.DFCSaidasOperacionais()
        self.saidas_nao_operacionais = finantialsSchemas.DFCSaidasNaoOperacionais()
        self.saidas = finantialsSchemas.DFCSaidas()
        self.cashflow = finantialsSchemas.DFC()
        self._loaded = False


    def _load_transactions(self):
        query = self.db.query(finantialsModels.Transactions)\
                .filter(finantialsModels.Transactions.company_id == self.company_id)\
                .filter(finantialsModels.Transactions.transaction_date >= self.date_begin_dt)\
                .filter(finantialsModels.Transactions.transaction_date <= self.date_end_dt).all()

        for item in query:
            value = abs(item.value or 0)

            # Transferências entre contas da mesma empresa não alteram o caixa
            # consolidado e, portanto, não entram nas entradas/saídas do DFC.
            if item.category == 5:
                continue

            if item.method:
                operational_entries = {
                    9: "vendas",
                    14: "recebimento_frete",
                    15: "reembolso_tarifas",
                }
                non_operational_entries = {
                    10: "rendimentos",
                    16: "entrada_emprestimo",
                    18: "rendimentos",
                    20: "resgate_aplicacoes",
                }

                if item.category in operational_entries:
                    field = operational_entries[item.category]
                    setattr(
                        self.entradas_operacionais,
                        field,
                        getattr(self.entradas_operacionais, field) + value
                    )
                elif item.category in non_operational_entries:
                    field = non_operational_entries[item.category]
                    setattr(
                        self.entradas_nao_operacionais,
                        field,
                        getattr(self.entradas_nao_operacionais, field) + value
                    )
                else:
                    self.entradas_operacionais.outros += value
                continue

            operational_outputs = {
                1: "fornecedores",
                2: "impostos",
                3: "fixos",
                4: "folha_salarial",
                6: "cartao_credito",
                8: "logistica",
                12: "compras",
                13: "devolucao_cliente",
                19: "publicidade",
                21: "devolucao_de_venda",
            }
            non_operational_outputs = {
                7: "distribuicao_lucros",
                11: "despesas_bancarias",
                17: "pagamento_emprestimo",
                20: "aplicacoes_financeiras",
            }

            if item.category in operational_outputs:
                field = operational_outputs[item.category]
                setattr(
                    self.saidas_operacionais,
                    field,
                    getattr(self.saidas_operacionais, field) + value
                )
            elif item.category in non_operational_outputs:
                field = non_operational_outputs[item.category]
                setattr(
                    self.saidas_nao_operacionais,
                    field,
                    getattr(self.saidas_nao_operacionais, field) + value
                )
            else:
                self.saidas_operacionais.outros += value

        self.entradas.entradas_operacionais = sum(
            value for _, value in self.entradas_operacionais
            if isinstance(value, (int, float))
        )
        self.entradas.entradas_nao_operacionais = sum(
            value for _, value in self.entradas_nao_operacionais
            if isinstance(value, (int, float))
        )
        self.saidas.saidas_operacionais = sum(
            value for _, value in self.saidas_operacionais
            if isinstance(value, (int, float))
        )
        self.saidas.saidas_nao_operacionais = sum(
            value for _, value in self.saidas_nao_operacionais
            if isinstance(value, (int, float))
        )
        self._loaded = True

    def _get_initial_balance(self):
        final_transactions = self.db.query(finantialsModels.Transactions)\
            .filter(finantialsModels.Transactions.company_id == self.company_id)\
            .filter(finantialsModels.Transactions.transaction_date <= self.date_end_dt)\
            .all()

        initial_transactions = self.db.query(finantialsModels.Transactions)\
            .filter(finantialsModels.Transactions.company_id == self.company_id)\
            .filter(finantialsModels.Transactions.transaction_date <= self.date_begin_dt)\
            .all()

        def calculate_balances(transactions):
            total = 0
            balances_by_bank = {}

            for item in transactions:
                value = abs(item.value or 0)
                signed_value = value if item.method else -value
                total += signed_value

                if item.bank_account_id is not None:
                    balances_by_bank[item.bank_account_id] = (
                        balances_by_bank.get(item.bank_account_id, 0) +
                        signed_value
                    )

            return total, balances_by_bank

        initial, initial_by_bank = calculate_balances(initial_transactions)
        final, final_by_bank = calculate_balances(final_transactions)

        bank_accounts = self.db.query(finantialsModels.Bank)\
            .filter(finantialsModels.Bank.company_id == self.company_id)\
            .order_by(finantialsModels.Bank.id)\
            .all()

        banks = [
            finantialsSchemas.DFCBankBalance(
                bank_id=bank.id,
                bank_name=bank.bank_name,
                bank_code=bank.bank_code,
                agency=bank.agency,
                account_number=bank.account_number,
                account_digit=bank.account_digit,
                saldo_inicial=initial_by_bank.get(bank.id, 0),
                saldo_final=final_by_bank.get(bank.id, 0),
            )
            for bank in bank_accounts
        ]

        return initial, final, banks


    def _load_future(self):
        # entradas de vendas
        def get_sales():
            from ..routers.mercado_livre import get_releases
            releases = get_releases(company_id=self.company_id, date=self.future_date_dt)
            n = 0
            futures = []
            for k, v in releases['per_day'].items():
                future_sales = finantialsSchemas.DFCFutureSales()
                n += v
                future_sales.date = k
                future_sales.value = v
                futures.append(future_sales)
            return n, futures

        def get_suppliers():
            query = self.db.query(suppliersModels.SupplierPayments)\
                    .filter(suppliersModels.SupplierPayments.company_id == self.company_id)\
                    .filter(suppliersModels.SupplierPayments.vencimento >= self.date_end_dt)\
                    .filter(suppliersModels.SupplierPayments.vencimento <= self.future_date_dt).all()

            futures = []
            n = 0
            for item in query:
                future_payments = finantialsSchemas.DFCFutureSales()
                future_payments.value = item.valor
                future_payments.date = item.vencimento
                futures.append(future_payments)
                n += item.valor

            return n, futures


        def get_taxes():
            query = self.db.query(finantialsModels.Taxes)\
                    .filter(finantialsModels.Taxes.company_id == self.company_id)\
                    .filter(finantialsModels.Taxes.payment_date >= self.date_end_dt)\
                    .filter(finantialsModels.Taxes.payment_date <= self.future_date_dt).all()

            futures = []
            n = 0
            for item in query:
                future_tax = finantialsSchemas.DFCFutureSales()
                future_tax.value = item.value
                future_tax.date = item.payment_date
                futures.append(future_tax)
                n += item.value

            return n, futures

        def get_payroll():
            query = self.db.query(accountModels.EmployeePayroll)\
                    .filter(accountModels.EmployeePayroll.company_id == self.company_id)\
                    .filter(accountModels.EmployeePayroll.data_vencimento >= self.date_end)\
                    .filter(accountModels.EmployeePayroll.data_vencimento <= self.future_date).all()

            futures = []
            n = 0
            for item in query:
                future_payroll = finantialsSchemas.DFCFutureSales()
                future_payroll.value = item.salario_liquido
                future_payroll.date = item.data_vencimento
                futures.append(future_payroll)
                n += item.salario_liquido

            return n, futures

        future = finantialsSchemas.DFCFuture()
        future.entrada_vendas, future.vendas_details = get_sales()
        future.pagamentos_fornecedores, future.fornecedores_details = get_suppliers()
        future.impostos, future.impostos_details = get_taxes()
        future.folha_salarial, future.folha_salarial_details = get_payroll()


        # custos fixos (previsão de impostos, folha, fornecedores)

        # pagamentos emprestimos, parcelas
        return future

    def get_cashflow(self, show_details=False):
        if not self._loaded:
            self._load_transactions()

        initial_balance, final_balance, banks_details = self._get_initial_balance()
        total_entries = (
            self.entradas.entradas_operacionais +
            self.entradas.entradas_nao_operacionais
        )
        total_outputs = (
            self.saidas.saidas_operacionais +
            self.saidas.saidas_nao_operacionais
        )

        self.entradas.entradas_operacionais_details = (
            self.entradas_operacionais if show_details else None
        )
        self.entradas.entradas_nao_operacionais_details = (
            self.entradas_nao_operacionais if show_details else None
        )
        self.saidas.saidas_operacionais_details = (
            self.saidas_operacionais if show_details else None
        )
        self.saidas.saidas_nao_operacionais_details = (
            self.saidas_nao_operacionais if show_details else None
        )

        operational_balance = (
            self.entradas.entradas_operacionais -
            self.saidas.saidas_operacionais
        )
        self.cashflow = finantialsSchemas.DFC(
            saldo_inicial=initial_balance,
            saldos_bancos=banks_details,
            entradas=self.entradas,
            total_entradas=total_entries,
            saidas=self.saidas,
            total_saidas=total_outputs,
            saldo_operacional=operational_balance,
            saldo_final=final_balance
        )
        if self.future_date_dt:
            self.cashflow.future = self._load_future()
            if not show_details:
                self.cashflow.future.vendas_details = None
                self.cashflow.future.fornecedores_details = None
                self.cashflow.future.impostos_details = None
                self.cashflow.future.folha_salarial_details = None
        return self.cashflow


class Bank:
    def __init__(
        self, 
        bank_id: int,
        db: Session = Depends(get_db)
        ):
        self.bank_id = bank_id
        self.db = db
        self.bank_name = None


    def _load_bank(self):
        query = self.db.query(finantialsModels.Bank).filter(finantialsModels.Bank.id == self.bank_id).first()
        self.id = query.id
        self.company_id = query.company_id 
        self.bank_name = query.bank_name 
        self.bank_code = query.bank_code 
        self.agency = query.agency 
        self.account_number = query.account_number 
        self.account_digit = query.account_digit 
        self.account_type = query.account_type 
        self.holder_name = query.holder_name 
        self.holder_document = query.holder_document 
        self.is_active = query.is_active 
        self.created_at = query.created_at 


    def get_bank(self):
        if not self.bank_name:
            self._load_bank()
        return finantialsSchemas.BankResponse(
            id=self.id,
            company_id=self.company_id,
            bank_name=self.bank_name,
            bank_code=self.bank_code,
            agency=self.agency,
            account_number=self.account_number,
            account_digit=self.account_digit,
            account_type=self.account_type,
            holder_document=self.holder_document,
            holder_name=self.holder_name,
            is_active=self.is_active,
            created_at=self.created_at
        )
