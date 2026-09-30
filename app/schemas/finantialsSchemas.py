from pydantic import BaseModel, Field
from pydantic import ConfigDict
from typing import Optional, List, Union
from .companySchemas import CompanyResponse
from datetime import datetime, date
from .supplierSchemas import Payments
from .productSchemas import ProductResponse
from decimal import Decimal


class CreditCardItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    data: Optional[datetime] = None
    tipo: Optional[str] = None
    descricao: Optional[str] = None
    valor: Optional[float] = None
    category: Optional[int] = None



class CreditCardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    bank_account_id: Optional[int] = None
    cartao: Optional[str] = None
    vencimento: Optional[datetime] = None
    saldo_fatura_anterior: Optional[float] = None
    lancamentos: Optional[float] = None
    encargos: Optional[float] = None
    total_fatura: Optional[float] = None
    items: List[CreditCardItemResponse]


class AtivoCirculante(BaseModel):
    caixa: Optional[float] = 0
    aplicacoes: Optional[float] = 0
    contas_a_receber: Optional[float] = 0
    estoque: Optional[float] = 0
    detalhamento_estoque: Optional[List[ProductResponse]] = []
    impostos_a_recuperar: Optional[float] = 0
    outros_creditos: Optional[float] = 0

class ImobilizadoDetail(BaseModel):
    item: Optional[str] = None
    value: Optional[float] = 0

class AtivoNaoCirculante(BaseModel):
    aplicacoes_financeiras: Optional[float] = 0
    contas_a_receber: Optional[float] = 0
    impostos_a_recuperar: Optional[float] = 0
    outros_creditos: Optional[float] = 0
    imobilizado: Optional[float] = 0
    imobilizado_detail: Optional[List[ImobilizadoDetail]] = []
    intangivel: Optional[float] = 0


class Ativo(BaseModel):
    total_ativo_circulante: Optional[float] = 0
    ativos_circulantes: Optional[AtivoCirculante] = None
    total_ativo_nao_circulante: Optional[float] = 0
    ativos_nao_circulantes: Optional[AtivoNaoCirculante] = None
    total_ativo: Optional[float] = 0



class PassivoCirculante(BaseModel):
    emprestimos_e_financiamentos: Optional[float] = 0
    arrendamento: Optional[float] = 0
    fornecedores: Optional[float] = 0
    fornecedores_detail: Optional[List[Payments]] = []
    outras_obrigacoes: Optional[float] = 0


class PassivoNaoCirculante(BaseModel):
    emprestimos_e_financiamentos: Optional[float] = 0
    fornecedores: Optional[float] = 0
    fornecedores_detail: Optional[Payments] = None
    outras_obrigacoes: Optional[float] = 0
    arrendamento: Optional[float] = 0


class Passivo(BaseModel):
    total_passivo_circulante: Optional[float] = 0
    passivos_circulantes: Optional[PassivoCirculante] = None
    total_passivo_nao_circulante: Optional[float] = 0
    passivos_nao_circulantes: Optional[PassivoNaoCirculante] = None
    total_passivo: Optional[float] = 0


class PatrimonioLiquidoDetalhado(BaseModel):
    capital_social: Optional[float] = 0
    reserva_de_capital: Optional[float] = 0
    reservas_de_lucros: Optional[float] = 0
    reserva_de_incentivos_fiscais: Optional[float] = 0
    outros_resultados_abrangentes: Optional[float] = 0
    lucros_acumulados: Optional[float] = 0
    dividendos_adicionais_propostos: Optional[float] = 0


class PatrimonioLiquido(BaseModel):
    patrimonio_liquido: Optional[float] = 0
    detalhes: Optional[PatrimonioLiquidoDetalhado] = None


class BalancoPatrimonial(BaseModel):
    ativo: Optional[Ativo] = None
    passivo: Optional[Passivo] = None
    patrimonio_liquido: Optional[PatrimonioLiquido] = None
    total_passivo_patrimonio_liquido: Optional[float] = 0


class ReceitaOperacionalBrutaDetail(BaseModel):
    invoice_number: Optional[str] = None
    value: Optional[float] = None
    date: Optional[datetime] = None

class ReceitaOperacionalBruta(BaseModel):
    vendas: Optional[float] = 0
    rendimentos: Optional[float] = 0
    details: Optional[List[ReceitaOperacionalBrutaDetail]] = []


class cmv_detail(BaseModel):
    compras: Optional[float] = 0
    estoque_passado: Optional[float] = 0
    estoque_atual: Optional[float] = 0


class TaxesDetails(BaseModel):
    transaction_id: Optional[int] = None
    name: Optional[str] = None
    detail: Optional[str] = None
    value: Optional[float] = None
    payment_date: Optional[datetime] = None

class DeducoesDeVenda(BaseModel):
    pis_cofins: Optional[float] = 0
    icms: Optional[float] = 0
    difal: Optional[float] = 0
    irrf: Optional[float] = 0
    iof: Optional[float] = 0
    tarifas: Optional[float] = 0
    comissoes: Optional[float] = 0
    despesas_administrativas: Optional[float] = 0
    despesas_bancarias: Optional[float] = 0
    frete: Optional[float] = 0
    custo_mercadoria_vendida: Optional[float] = 0
    cmv_details: Optional[cmv_detail] = None
    custo_mercadoria_vendida_details: Optional[List[ProductResponse]] = []
    taxes_details: Optional[List[TaxesDetails]] = []

class GastosVariaveis(BaseModel):
    cartao_de_credito: Optional[float] = 0
    insumos: Optional[float] = 0

class CustosFixos(BaseModel):
    software: Optional[float] = 0
    aluguel: Optional[float] = 0
    contabilidade: Optional[float] = 0
    pro_labore: Optional[float] = 0
    aluguel: Optional[float] = 0
    folha_salarial: Optional[float] = 0
    internet: Optional[float] = 0
    luz: Optional[float] = 0
    agua: Optional[float] = 0
    outros: Optional[float] = 0

class Investimentos(BaseModel):
    publicidade: Optional[float] = 0
    caixa: Optional[float] = 0


class DRE(BaseModel):
    date_begin: Optional[datetime] = None
    date_end: Optional[datetime] = None
    faturamento: Optional[float] = 0
    receita_operacional_bruta: Optional[ReceitaOperacionalBruta] = None
    total_deducoes_de_venda: Optional[float] = 0
    deducoes_de_venda: Optional[DeducoesDeVenda] = None
    receita_liquida_de_vendas: Optional[float] = 0
    total_gastos_variaveis: Optional[float] = 0
    gastos_variaveis: Optional[GastosVariaveis] = None
    lucro_bruto: Optional[float] = 0
    margem_contribuicao: Optional[float] = 0
    total_custos_fixos: Optional[float] = 0
    custos_fixos: Optional[CustosFixos] = None
    lucro_operacional: Optional[float] = 0
    total_investimentos: Optional[float] = 0
    investimentos: Optional[Investimentos] = None
    distribuicao_lucros: Optional[float] = 0
    ponto_de_equilibrio_contabil: Optional[float] = 0
    ponto_de_equilibrio_economico: Optional[float] = 0


class DFCEntradasOperacionais(BaseModel):
    vendas: float = 0
    a_receber: float = 0
    recebimento_frete: float = 0
    reembolso_tarifas: float = 0
    outros: float = 0

class DFCEntradasNaoOperacionais(BaseModel):
    entrada_emprestimo: float = 0
    rendimentos: float = 0
    resgate_aplicacoes: float = 0
    outros: float = 0


class DFCEntradas(BaseModel):
    entradas_operacionais: float = 0
    entradas_operacionais_details: Optional[DFCEntradasOperacionais] = None
    entradas_nao_operacionais: float = 0
    entradas_nao_operacionais_details: Optional[DFCEntradasNaoOperacionais] = None

class DFCSaidasOperacionais(BaseModel):
    fornecedores: float = 0
    impostos: float = 0
    impostos_details: Optional[DeducoesDeVenda] = None
    fixos: float = 0
    fixos_details: Optional[CustosFixos] = None
    cartao_credito: float = 0
    folha_salarial: float = 0
    logistica: float = 0
    compras: float = 0
    devolucao_cliente: float = 0
    devolucao_de_venda: float = 0
    publicidade: float = 0
    outros: float = 0

class DFCSaidasNaoOperacionais(BaseModel):
    despesas_bancarias: float = 0
    pagamento_emprestimo: float = 0
    aplicacoes_financeiras: float = 0
    distribuicao_lucros: float = 0
    outros: float = 0


class DFCSaidas(BaseModel):
    saidas_operacionais: float = 0
    saidas_operacionais_details: Optional[DFCSaidasOperacionais] = None
    saidas_nao_operacionais: float = 0
    saidas_nao_operacionais_details: Optional[DFCSaidasNaoOperacionais] = None



class DFCFutureSales(BaseModel):
    date: Optional[datetime] = None
    value: Optional[float] = None

class DFCFuture(BaseModel):
    entrada_vendas: Optional[float] = None
    vendas_details: Optional[List[DFCFutureSales]] = []
    pagamentos_fornecedores: Optional[float] = None
    fornecedores_details: Optional[List[DFCFutureSales]] = []
    folha_salarial: Optional[float] = None
    folha_salarial_details: Optional[List[DFCFutureSales]] = []
    impostos: Optional[float] = None
    impostos_details: Optional[List[DFCFutureSales]] = []


class DFCBankBalance(BaseModel):
    bank_id: int
    bank_name: str
    bank_code: Optional[str] = None
    agency: Optional[str] = None
    account_number: Optional[str] = None
    account_digit: Optional[str] = None
    saldo_inicial: float = 0
    saldo_final: float = 0



class DFC(BaseModel):
    saldo_inicial: Optional[float] = None
    saldos_bancos: List[DFCBankBalance] = Field(default_factory=list)
    entradas: Optional[DFCEntradas] = None
    total_entradas: Optional[float] = None
    saidas: Optional[DFCSaidas] = None
    total_saidas: Optional[float] = None
    saldo_operacional: Optional[float] = None
    saldo_final: Optional[float] = None
    future: Optional[DFCFuture] = None



'''
    Fazer a parte de compras
    Compras totais, por fornecedor e por produto
'''


    
class InvoiceItemBase(BaseModel):
    id: Optional[int] = None
    invoice_id: Optional[int] = None
    n_item: Optional[int] = None
    c_prod: Optional[str] = None
    ean: Optional[str] = None
    x_prod: Optional[str] = None
    ncm: Optional[str] = None
    cest: Optional[str] = None
    cfop: Optional[str] = None
    u_com: Optional[str] = None
    q_com: Optional[Union[int, float]] = None
    v_un_com: Optional[float] = None
    v_prod: Optional[float] = None
    ean_trib: Optional[str] = None
    u_trib: Optional[str] = None
    q_trib: Optional[float] = None
    v_un_trib: Optional[float] = None
    x_ped: Optional[str] = None
    n_item_ped: Optional[str] = None
    invoice: Optional[str] = None
    tax_lines: Optional[str] = None

class InvoiceBase(BaseModel):
    id: Optional[int] = None
    chave_acesso: Optional[str] = None
    tp_amb: Optional[str] = None
    modelo: Optional[str] = None
    serie: Optional[str] = None
    numero: Optional[str] = None
    tp_nf: Optional[str] = None
    fin_nfe: Optional[str] = None
    nat_op: Optional[str] = None
    id_dest: Optional[str] = None

        #: Optional[str] = None
    dh_emissao: Optional[datetime] = None
    dh_saida_entrada: Optional[datetime] = None

        #: Optional[str] = None
    cnpj_emit: Optional[str] = None
    ie_emit: Optional[str] = None
    crt_emit: Optional[str] = None
    uf_emit: Optional[str] = None
    mun_emit: Optional[str] = None

    cnpj_dest: Optional[str] = None
    ie_dest: Optional[str] = None
    ind_ie_dest: Optional[str] = None
    uf_dest: Optional[str] = None
    mun_dest: Optional[str] = None

    cstat: Optional[str] = None
    xmotivo: Optional[str] = None
    nprot: Optional[str] = None
    dh_recibo: Optional[datetime] = None

    v_prod: Optional[float] = None
    v_nf: Optional[float] = None
    v_desc: Optional[float] = None
    v_frete: Optional[float] = None
    v_outro: Optional[float] = None
    v_seg: Optional[float] = None
    v_bc_icms: Optional[float] = None
    v_icms: Optional[float] = None
    v_st: Optional[float] = None
    v_ipi: Optional[float] = None
    v_pis: Optional[float] = None
    v_cofins: Optional[float] = None
    v_bc_ibs_cbs: Optional[float] = None
    v_ibs: Optional[float] = None
    v_ibs_uf: Optional[float] = None
    v_ibs_mun: Optional[float] = None
    v_cbs: Optional[float] = None
    items: Optional[List[InvoiceItemBase]] = None

class InvoicesReq(BaseModel):
    invoices: Optional[List[InvoiceBase]] = None


class TaxesBase(BaseModel):

    class Infos(BaseModel):
        id: Optional[int] = None
        invoice_id: Optional[int] = None
        item_id: Optional[int] = None
        tax: Optional[str] = None
        cst: Optional[str] = None
        class_trib: Optional[str] = None
        orig: Optional[str] = None
        mod_bc: Optional[str] = None
        v_bc: Optional[float] = None
        p_aliq: Optional[float] = None
        v_trib: Optional[float] = None
        uf: Optional[str] = None
        mun: Optional[str] = None

    taxes: Optional[List[Infos]] = None


class ProductPurchaseItem(BaseModel):
    invoice: InvoiceBase
    item: InvoiceItemBase
    taxes: TaxesBase

    # meta_json = Column(JSON, nullable=True)

class ProductPurchaseResults(BaseModel):
    quantity: int = 0
    v_prod: float = 0
    invoices: List[ProductPurchaseItem] = Field(default_factory=list)


class ProductSaleItem(BaseModel):
    invoice: InvoiceBase
    item: InvoiceItemBase
    taxes: TaxesBase


class ProductSaleResults(BaseModel):
    quantity: int = 0
    v_prod: float = 0
    invoices: List[ProductSaleItem] = Field(default_factory=list)

class EventsBase(BaseModel):
    pass


class SellTaxesBase(BaseModel):
    company_id: int
    taxes_name: str
    detail: str
    value: float
    reference: Optional[datetime] = datetime.now()
    payment_date: Optional[datetime] = datetime.now()

class SellTaxesCreate(SellTaxesBase):
    pass

class SellTaxesResponse(SellTaxesBase):
    id: Optional[int] = None



class FixosBase(BaseModel):
    company_id: int
    name: str
    detail: str
    value: float
    payment_date: Optional[datetime] = datetime.now()

class FixosCreate(FixosBase):
    pass

class FixosResponse(FixosBase):
    id: Optional[int] = None


class MercadoLivreBillingItem(BaseModel):
    id: Optional[int] = None
    company_id: Optional[int] = None
    data_tarifa: Optional[str] = None
    numero_tarifa: Optional[int] = None
    detalhe: Optional[str] = None
    valor: Optional[float] = None
    envio_cliente: Optional[float] = None
    order_id: Optional[str] = None


class FreightCostsTM(BaseModel):
    id: Optional[int] = None
    company_id: Optional[int] = None
    remessa: Optional[int] = None
    data_pedido: Optional[datetime] = None
    data_coleta: Optional[datetime] = None
    data_contabil: Optional[datetime] = None
    servico: Optional[str] = None
    cep_dest: Optional[str] = None
    nota_fiscal: Optional[str] = None
    volumes: Optional[int] = None
    peso: Optional[float] = None
    valor: Optional[float] = None


class ShopeeTariffs(BaseModel):
    id: Optional[int] = None
    company_id: Optional[int] = None
    numero_nota: Optional[str] = None
    data_emissao: Optional[datetime] = None
    prestador_cnpj: Optional[str] = None
    tomador_cnpj: Optional[str] = None
    descricao: Optional[str] = None
    data_referencia: Optional[datetime] = None
    valor: Optional[float] = None


class BankBase(BaseModel):
    company_id: int
    bank_name: str
    bank_code: Optional[str] = None
    agency: Optional[str] = None
    account_number: Optional[str] = None
    account_digit: Optional[str] = None
    account_type: Optional[str] = None
    holder_document: Optional[str] = None
    holder_name: Optional[str] = None
    is_active: Optional[bool] = True
    created_at: Optional[datetime] = None


class BankCreate(BankBase):
    pass

class BankResponse(BankBase):
    id: Optional[int] = None


class AttributePayment(BaseModel):
    transaction_id: int
    category_id: Optional[int] = None
    item_id: Optional[int] = None


class AttributeCreditCardItem(BaseModel):
    item_id: int
    category_id: Optional[int] = None
    motive_id: Optional[int] = None


# Compatibilidade temporaria para imports antigos; o contrato da API agora e
# categoria + motivo, como em AttributePayment.
AttributeCreditCardPurchase = AttributeCreditCardItem


class EditTransaction(BaseModel):
    transaction_id: int
    counterparty_document: str


class TransactionCategoryCreate(BaseModel):
    name: str

class TransactionCategoryResponse(TransactionCategoryCreate):
    id: int


class DreResultado(BaseModel):
    """Contrato novo: usar este modelo no response_model da rota de DRE.

    Valores monetários são Decimal (JSON padrão do Pydantic: strings).
    Margens são frações: 0.10 significa 10%. Não usar o schema DRE antigo:
    ele não contém CMV separado, financeiro, pendências nem lucro líquido.
    """

    date_begin: date
    date_end: date
    faturamento: Decimal
    receita_operacional_bruta: dict
    total_deducoes_de_venda: Decimal
    deducoes_de_venda: dict
    receita_liquida_de_vendas: Decimal
    custo_mercadoria_vendida: Decimal
    cmv_details: dict
    lucro_bruto: Decimal
    total_gastos_variaveis: Decimal
    gastos_variaveis: dict
    margem_contribuicao_valor: Decimal
    margem_contribuicao: Optional[Decimal]
    total_custos_fixos: Decimal
    custos_fixos: dict
    lucro_operacional: Decimal
    receitas_financeiras: dict
    despesas_financeiras: dict
    resultado_financeiro: Decimal
    resultado_antes_irpj_csll: Decimal
    tributos_sobre_lucro: dict
    lucro_liquido: Optional[Decimal]
    fora_da_dre: dict
    distribuicao_lucros: Decimal
    ponto_de_equilibrio_contabil: Optional[Decimal]
    ponto_de_equilibrio_economico: Optional[Decimal]
    provisorio: bool
    avisos: List[str]
    pendencias: List[dict]
    detalhes: Optional[dict] = None
