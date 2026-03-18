from pydantic import BaseModel
from typing import Optional, List
from .companySchemas import CompanyResponse
from datetime import datetime


class QueryBase(BaseModel):
    company_id: Optional[datetime] = None
    date_begin: Optional[datetime] = None
    date_end: Optional[datetime] = None


class DividasBase(BaseModel):
    fornecedor: Optional[float] = 0
    impostos: Optional[float] = 0

class DividasInfo(BaseModel):
    total: Optional[float] = 0
    detail: Optional[DividasBase] = None


class buyInfos(BaseModel):
    total: Optional[float] = 0


class salesInfo(BaseModel):
    total: Optional[float] = 0


class FinantialsResume(BaseModel):
    company: Optional[CompanyResponse] = None
    dividas: Optional[DividasInfo] = None
    vendas: Optional[salesInfo] = None
    compras: Optional[buyInfos] = None
    
    

class InvoiceBase(BaseModel):
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

class InvoicesReq(BaseModel):
    invoices: Optional[List[InvoiceBase]] = None

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
