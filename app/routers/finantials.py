from datetime import datetime
from fastapi import APIRouter, Depends, UploadFile, File
from ..schemas import finantialsSchemas
from ..oauth2 import get_current_user
from ..server_config import API_URL
import requests, json
from typing import Optional, Union, List
from ..services import userServices, mercadoLivreServices
from sqlalchemy.orm import Session
from ..database import get_db
from ..services import userServices
from calendar import monthrange
from .suppliers import get_payments
from .mercado_livre import get_infos

router = APIRouter(
    prefix="/finantials",
    tags=["Finantials"]
)


@router.post("/upload-xml")
def upload_invoice_xml(
    xml_file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    url = f"{API_URL}/invoices/upload"  # endpoint da primeira função

    req = requests.post(
        url,
        files={
            "xml_file": (
                xml_file.filename,
                xml_file.file,  # envia o stream direto
                xml_file.content_type or "application/xml",
            )
        },
        timeout=60,
    )

    return req.json()


def get_invoices(
    cnpj: str, 
    date_begin: Optional[str] = None,
    date_end: Optional[str] = None,
    emit: bool = False
    ):
    url = f"{API_URL}/invoices"
    params = {
        "cnpj": cnpj,
        "emit": emit,
        "date_begin": date_begin,
        "date_end": date_end
    }
    req = requests.get(url=url, timeout=30, params=params)
    if req.status_code == 200:
        data = req.json()
        return data

# @router.get("/resume")
# def generate_resume(
#     current_user=Depends(get_current_user),
#     date_begin: Optional[str] = None,
#     date_end: Optional[str] = None,
#     db: Session = Depends(get_db)
# ):
#     user = userServices.User(user=current_user, db=db)
#     companies = user.companies

#     if not date_begin or not date_end:
#         date_begin, date_end = get_dates()

#     final_result = []
#     for comp in companies:
#         result = finantialsSchemas.FinantialsResume(
#             company=comp
#         )
#         result.dividas = process_dividas(company_id=comp.id, date_begin=date_begin, date_end=date_end, current_user=current_user, db=db)

#         sales_info = finantialsSchemas.salesInfo()
#         buy_infos = finantialsSchemas.buyInfos()

#         vendas_req = get_invoices(cnpj=comp.cnpj, date_begin=date_begin, date_end=date_end, emit=True)
#         compras_req = get_invoices(cnpj=comp.cnpj, date_begin=date_begin, date_end=date_end)
#         # print(json.dumps(vendas_req, indent=4))

#         vendas = finantialsSchemas.InvoicesReq.model_validate(vendas_req)
#         # print(vendas)
#         sales_info.total = sum([item.v_nf for item in vendas.invoices])
#         compras = finantialsSchemas.InvoicesReq.model_validate(compras_req)
#         buy_infos.total = sum([item.v_nf for item in compras.invoices])
            

#         result.vendas = sales_info
#         result.compras = buy_infos


#         final_result.append(result)

#     return final_result


# def get_dates():
#     now = datetime.now()
#     start_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
#     last_day = monthrange(now.year, now.month)[1]
#     end_month = now.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)
#     date_begin = start_month.strftime("%Y-%m-%d %H:%M:%S")
#     date_end = end_month.strftime("%Y-%m-%d %H:%M:%S")
#     return date_begin, date_end


def process_dividas(
    company_id: int,
    date_begin: Optional[str] = None,
    date_end: Optional[str] = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    div_base = finantialsSchemas.DividasBase()
    supplier_to_pay = get_payments(company_id=company_id, date_begin=date_begin, date_end=date_end, db=db, current_user=current_user)
    div_base.fornecedor += supplier_to_pay.total
    div_info = finantialsSchemas.DividasInfo(
        detail=div_base,
        total=div_base.fornecedor + div_base.impostos
    )

    return div_info