from pydantic import BaseModel
from typing import Optional, List
from .companySchemas import CompanyResponse
from datetime import datetime
from .supplierSchemas import Payments
from .productSchemas import ProductResponse


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



class ReceitaOperacionalBruta(BaseModel):
    vendas: Optional[float] = 0


class cmv_detail(BaseModel):
    compras: Optional[float] = 0
    estoque_passado: Optional[float] = 0
    estoque_atual: Optional[float] = 0

class DeducoesDeVenda(BaseModel):
    pis: Optional[float] = 0
    cofins: Optional[float] = 0
    icms: Optional[float] = 0
    difal: Optional[float] = 0
    irrf: Optional[float] = 0
    tarifas: Optional[float] = 0
    comissoes: Optional[float] = 0
    frete: Optional[float] = 0
    custo_mercadoria_vendida: Optional[float] = 0
    cmv_details: Optional[cmv_detail] = None
    custo_mercadoria_vendida_details: Optional[List[ProductResponse]] = []

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

class Investimentos(BaseModel):
    publicidade: Optional[float] = 0



class DRE(BaseModel):
    faturamento: Optional[float] = 0
    receita_operacional_bruta: Optional[ReceitaOperacionalBruta] = None
    total_deducoes_de_venda: Optional[float] = 0
    deducoes_de_venda: Optional[DeducoesDeVenda] = None
    receita_liquida_de_vendas: Optional[float] = 0
    total_gastos_variaveis: Optional[float] = 0
    gastos_variaveis: Optional[GastosVariaveis] = None
    lucro_bruto: Optional[float] = 0
    total_custos_fixos: Optional[float] = 0
    custos_fixos: Optional[CustosFixos] = None
    lucro_operacional: Optional[float] = 0
    total_investimentos: Optional[float] = 0
    investimentos: Optional[Investimentos] = None






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
    q_com: Optional[int] = None
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

    # meta_json = Column(JSON, nullable=True)

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