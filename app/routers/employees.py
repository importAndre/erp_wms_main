from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session, joinedload
from ..models import accountModels
from ..schemas import employeesSchemas
from ..services import employeeServices
from ..database import get_db
from ..oauth2 import get_current_user
from typing import Union, List, Optional
from sqlalchemy.exc import IntegrityError
import os
from io import BytesIO
from PyPDF2 import PdfReader
import re
from datetime import datetime
from calendar import monthrange

router = APIRouter(
    prefix="/employees",
    tags=["employees"],
    responses={404: {"description": "Not found"}},
)

@router.get("/")
def get_employees(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission Denied")
    return db.query(accountModels.Employee).all()


@router.post("/register")
def register_employee(
    employee: employeesSchemas.EmployeeRegister,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_employee = accountModels.Employee(
        first_name=employee.first_name,
        last_name=employee.last_name,
        email=employee.email,
        phone_number=employee.phone_number,
        cpf=employee.cpf,
        position=employee.position,
        department=employee.department,
        hire_date=employee.hire_date,
        salary=employee.salary,
        cbo=employee.cbo,
        pis=employee.pis,
        ctps=employee.ctps,
        serie=employee.serie,
        is_active=employee.is_active,
        company_id=employee.company_id,
        user_id=employee.user_id
    )
    db.add(new_employee)
    db.commit()
    db.refresh(new_employee)

    return new_employee


@router.get("/search/{emp_id}", response_model=Union[employeesSchemas.EmployeeResponse, List[employeesSchemas.EmployeeResponse]])
def get_employee(
    emp_id: Optional[int] = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Union[employeesSchemas.EmployeeResponse, List[employeesSchemas.EmployeeResponse]]:

    if not emp_id:
        employees = db.query(accountModels.Employee).all()
        return [employeeServices.Employee(emp_id=emp.id, db=db).get_employee() for emp in employees]
    return employeeServices.Employee(emp_id=emp_id, db=db).get_employee()



@router.post("/register-payroll", response_model=employeesSchemas.EmployeePayrollResponse)
def register_payroll(
    infos: employeesSchemas.EmployeePayrollCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission Denied"
        )

    emp = db.query(accountModels.Employee).filter(
        accountModels.Employee.id == infos.employee_id
    ).first()

    if not emp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Funcionário não encontrado"
        )

    try:
        payroll = accountModels.EmployeePayroll(
            employee_id=infos.employee_id,
            company_id=infos.company_id,
            ano_referencia=infos.ano_referencia,
            mes_referencia=infos.mes_referencia,
            data_competencia=infos.data_competencia,
            data_vencimento=infos.data_vencimento,
            data_pagamento=infos.data_pagamento,
            salario_base=infos.salario_base or 0,
            horas_mensais=infos.horas_mensais or 0,
            base_inss=infos.base_inss or 0,
            valor_inss=infos.valor_inss or 0,
            base_fgts=infos.base_fgts or 0,
            valor_fgts=infos.valor_fgts or 0,
            base_irrf=infos.base_irrf or 0,
            valor_irrf=infos.valor_irrf or 0,
            base_rais=infos.base_rais or 0,
            base_salario_familia=infos.base_salario_familia or 0,
            total_proventos=infos.total_proventos or 0,
            total_descontos=infos.total_descontos or 0,
            salario_liquido=infos.salario_liquido or 0,
            status=infos.status or "pendente",
            paid=infos.paid if infos.paid is not None else False,
            observacoes=infos.observacoes
        )

        for item in infos.items:
            payroll.items.append(
                accountModels.EmployeePayrollItem(
                    codigo=item.codigo,
                    descricao=item.descricao,
                    tipo=item.tipo,
                    referencia=item.referencia or 0,
                    valor=item.valor,
                )
            )

        db.add(payroll)
        db.commit()
        db.refresh(payroll)

        result = db.query(accountModels.EmployeePayroll).options(
            joinedload(accountModels.EmployeePayroll.employee),
            joinedload(accountModels.EmployeePayroll.items)
        ).filter(
            accountModels.EmployeePayroll.id == payroll.id
        ).first()

        return result

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erro ao registrar folha de pagamento"
        )
    

@router.get("/payroll")
def get_payroll(
    emp_id: Optional[int] = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if emp_id:
        emp = employeeServices.Employee(emp_id=emp_id, db=db)
        return {
            "employee": emp.get_employee(),
            "payroll": emp.get_payroll()
        }
    else:
        query = db.query(accountModels.Employee).all()
        result = []
        for e in query:
            emp = employeeServices.Employee(emp_id=e.id, db=db)
            result.append({
                "employee": emp.get_employee(),
                "payroll": emp.get_payroll()
            })
        return result
 


MESES_MAP = {
    "JANEIRO": 1,
    "FEVEREIRO": 2,
    "MARÇO": 3,
    "MARCO": 3,
    "ABRIL": 4,
    "MAIO": 5,
    "JUNHO": 6,
    "JULHO": 7,
    "AGOSTO": 8,
    "SETEMBRO": 9,
    "OUTUBRO": 10,
    "NOVEMBRO": 11,
    "DEZEMBRO": 12,
}


def only_digits(value: Optional[str]) -> str:
    if not value:
        return ""
    return re.sub(r"\D", "", value)


def br_to_float(value: Optional[str]) -> float:
    if not value:
        return 0.0
    value = value.strip()
    value = value.replace(".", "").replace(",", ".")
    try:
        return float(value)
    except ValueError:
        return 0.0


def parse_date_br(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    value = value.strip()
    try:
        return datetime.strptime(value, "%d/%m/%Y")
    except ValueError:
        return None


def detect_pdf_type(text: str) -> str:
    text_upper = text.upper()

    if "ADIANTAMENTO SALARIAL" in text_upper:
        return "advance"

    if "ESPelho E RESUMO DA FOLHA MENSAL".upper() in text_upper or "REFERENTE AO MÊS DE" in text_upper:
        return "payroll"

    return "unknown"


def parse_reference_from_text(text: str):
    """
    Aceita:
    1) referente ao mês de JANEIRO/2026
    2) adiantamento salarial de 01/03/2026 até 31/03/2026
    """
    # folha mensal
    match_month_name = re.search(
        r"referente ao mês de\s+([A-ZÇÃÕÁÉÍÓÚ]+)\s*/\s*(\d{4})",
        text,
        re.IGNORECASE
    )
    if match_month_name:
        mes_nome = match_month_name.group(1).upper().strip()
        ano = int(match_month_name.group(2))
        mes = MESES_MAP.get(mes_nome)

        if not mes:
            raise HTTPException(
                status_code=400,
                detail=f"Mês de referência inválido no PDF: {mes_nome}"
            )

        return mes, ano

    # adiantamento
    match_period = re.search(
        r"adiantamento salarial de\s*(\d{2}/\d{2}/\d{4})\s*até\s*(\d{2}/\d{2}/\d{4})",
        text,
        re.IGNORECASE
    )
    if match_period:
        data_inicio = parse_date_br(match_period.group(1))
        if not data_inicio:
            raise HTTPException(
                status_code=400,
                detail="Não foi possível interpretar a data inicial do período de adiantamento."
            )
        return data_inicio.month, data_inicio.year

    raise HTTPException(
        status_code=400,
        detail="Não foi possível identificar o mês/ano de referência no PDF."
    )


def parse_advance_payment_date(text: str) -> Optional[datetime]:
    """
    Procura algo como:
    20/03/2026 Adiantamento em:
    """
    match = re.search(
        r"(\d{2}/\d{2}/\d{4})\s+Adiantamento em:",
        text,
        re.IGNORECASE
    )
    if not match:
        return None
    return parse_date_br(match.group(1))


def split_employee_blocks(text: str) -> List[str]:
    text = text.replace("\r", "")
    text = re.sub(r"[ \t]+", " ", text)

    start_pattern = re.compile(
        r"(?=(?:^|\n)\d+[A-ZÀ-Ú][A-ZÀ-Ú\s\-]*Admissão em \d{2}/\d{2}/\d{4})",
        re.MULTILINE
    )

    starts = [m.start() for m in start_pattern.finditer(text)]
    if not starts:
        return []

    blocks = []
    for i, start in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else len(text)
        block = text[start:end].strip()

        resumo_pos = block.find("PROVENTOS DESCONTOS")
        if resumo_pos != -1:
            block = block[:resumo_pos].strip()

        resumo_geral_pos = block.find("RESUMO GERAL")
        if resumo_geral_pos != -1:
            block = block[:resumo_geral_pos].strip()

        previd_pos = block.find("Previdenciários")
        if previd_pos != -1:
            block = block[:previd_pos].strip()

        if "Admissão em" in block and "CPF:" in block:
            blocks.append(block)

    return blocks


def extract_employee_header(block: str) -> dict:
    one_line = re.sub(r"\s+", " ", block).strip()

    name_match = re.search(
        r"^\d+([A-ZÀ-Ú][A-ZÀ-Ú\s\-]+?)Admissão em",
        one_line
    )
    admissao_match = re.search(r"Admissão em (\d{2}/\d{2}/\d{4})", one_line)
    salario_match = re.search(r"Salário base ([\d\.,]+)", one_line)
    horas_match = re.search(r"Horas mensais:\s*([\d\.,]+)", one_line)
    cpf_match = re.search(r"CPF:\s*([\d\.\-]+)", one_line)
    ctps_match = re.search(r"CTPS:\s*([\d\.]+)", one_line)
    cbo_match = re.search(r"CBO:\s*(\d+)", one_line)
    funcao_match = re.search(r"Função:\s*(.+?)(?=Total de proventos|Líquido|IR - >|Base INSS|Base Rais|$)", one_line)

    nome = name_match.group(1).strip() if name_match else None
    admissao = parse_date_br(admissao_match.group(1)) if admissao_match else None
    salario_base = br_to_float(salario_match.group(1)) if salario_match else 0.0
    horas_mensais = br_to_float(horas_match.group(1)) if horas_match else 0.0
    cpf = cpf_match.group(1).strip() if cpf_match else None
    ctps = only_digits(ctps_match.group(1)) if ctps_match else None
    cbo = cbo_match.group(1).strip() if cbo_match else None
    funcao = funcao_match.group(1).strip() if funcao_match else None

    return {
        "nome": nome,
        "admissao": admissao,
        "salario_base": salario_base,
        "horas_mensais": horas_mensais,
        "cpf": cpf,
        "ctps": ctps,
        "cbo": cbo,
        "funcao": funcao,
    }


def extract_totals(block: str) -> dict:
    one_line = re.sub(r"\s+", " ", block).strip()

    total_proventos_match = re.search(r"Total de proventos - >\s*([\d\.,]+)", one_line)
    total_descontos_match = re.search(r"Total de descontos - >\s*([\d\.,]+)", one_line)
    liquido_match = re.search(r"Líquido - >\s*([\d\.,]+)", one_line)
    base_rais_match = re.search(r"Base Rais\s*([\d\.,]+)", one_line)
    base_sf_match = re.search(r"Base salário família\s*([\d\.,]+)", one_line)

    folha_match = re.search(
        r"Folha\s+([\d\.,]+)\s+([\d\.,]+)\s+([\d\.,]+)\s+([\d\.,]+)\s+([\d\.,]+)",
        one_line
    )

    base_inss = valor_inss = base_irrf = valor_fgts = base_fgts = 0.0
    if folha_match:
        base_inss = br_to_float(folha_match.group(1))
        valor_inss = br_to_float(folha_match.group(2))
        base_irrf = br_to_float(folha_match.group(3))
        valor_fgts = br_to_float(folha_match.group(4))
        base_fgts = br_to_float(folha_match.group(5))

    ir_linha_match = re.search(r"IR - >\s*([\d\.,]+)", one_line)
    if ir_linha_match:
        base_irrf = br_to_float(ir_linha_match.group(1))

    return {
        "total_proventos": br_to_float(total_proventos_match.group(1)) if total_proventos_match else 0.0,
        "total_descontos": br_to_float(total_descontos_match.group(1)) if total_descontos_match else 0.0,
        "salario_liquido": br_to_float(liquido_match.group(1)) if liquido_match else 0.0,
        "base_rais": br_to_float(base_rais_match.group(1)) if base_rais_match else 0.0,
        "base_salario_familia": br_to_float(base_sf_match.group(1)) if base_sf_match else 0.0,
        "base_inss": base_inss,
        "valor_inss": valor_inss,
        "base_irrf": base_irrf,
        "valor_fgts": valor_fgts,
        "base_fgts": base_fgts,
        "valor_irrf": 0.0,
    }


def extract_items(block: str) -> List[dict]:
    items = []
    one_line = re.sub(r"\s+", " ", block).strip()

    section_match = re.search(
        r"Função:\s*.+?(?P<section>.+?)Total de proventos - >",
        one_line
    )

    if not section_match:
        return items

    section = section_match.group("section").strip()
    section = section.replace("PROVENTOS REFERÊNCIA VALOR DESCONTOS REFERÊNCIA VALOR", "").strip()

    # 1) padrão folha: provento + desconto na mesma linha
    pair_matches = re.finditer(
        r"(?P<ref_prov>\d{1,3},\d{2})\s+"
        r"(?P<valor_prov>\d{1,3}(?:\.\d{3})*,\d{2})\s+"
        r"(?P<desc_prov>.+?)"
        r"(?P<codigo_prov>\d{1,6})\s+"
        r"(?P<ref_desc>\d{1,3},\d{2})\s+"
        r"(?P<valor_desc>\d{1,3}(?:\.\d{3})*,\d{2})\s+"
        r"(?P<desc_desc>.+?)\s+"
        r"(?P<codigo_desc>\d{1,6})(?=\s|$)",
        section
    )
    for match in pair_matches:
        items.append({
            "codigo": match.group("codigo_prov"),
            "descricao": match.group("desc_prov").strip(),
            "tipo": "provento",
            "referencia": br_to_float(match.group("ref_prov")),
            "valor": br_to_float(match.group("valor_prov")),
        })
        items.append({
            "codigo": match.group("codigo_desc"),
            "descricao": match.group("desc_desc").strip(),
            "tipo": "desconto",
            "referencia": br_to_float(match.group("ref_desc")),
            "valor": br_to_float(match.group("valor_desc")),
        })

    # 2) padrão folha: desconto sozinho com referência
    single_discount_matches = re.finditer(
        r"(?<!\d)"
        r"(?P<ref>\d{1,3},\d{2})\s+"
        r"(?P<valor>\d{1,3}(?:\.\d{3})*,\d{2})\s+"
        r"(?P<desc>(?:Vale transporte|Adiantamento com ded\. IR|INSS|INSS pro-labore).+?)\s+"
        r"(?P<codigo>\d{1,6})(?=\s|$)",
        section
    )
    for match in single_discount_matches:
        items.append({
            "codigo": match.group("codigo"),
            "descricao": match.group("desc").strip(),
            "tipo": "desconto",
            "referencia": br_to_float(match.group("ref")),
            "valor": br_to_float(match.group("valor")),
        })

    # 3) padrão adiantamento: valor + descrição + código, sem referência
    advance_matches = re.finditer(
        r"(?<!\d)"
        r"(?P<valor>\d{1,3}(?:\.\d{3})*,\d{2})\s+"
        r"(?P<desc>Adiantamento salarial com IR)\s+"
        r"(?P<codigo>\d{1,6})(?=\s|$)",
        section,
        re.IGNORECASE
    )
    for match in advance_matches:
        items.append({
            "codigo": match.group("codigo"),
            "descricao": match.group("desc").strip(),
            "tipo": "provento",
            "referencia": 0.0,
            "valor": br_to_float(match.group("valor")),
        })

    # 4) fallback geral: valor + descrição + código
    generic_single_matches = re.finditer(
        r"(?<!\d)"
        r"(?P<valor>\d{1,3}(?:\.\d{3})*,\d{2})\s+"
        r"(?P<desc>[A-Za-zÀ-Úà-ú0-9\-\.\s\/]+?)\s+"
        r"(?P<codigo>\d{1,6})(?=\s|$)",
        section
    )
    for match in generic_single_matches:
        desc = match.group("desc").strip()

        if len(desc) < 3:
            continue

        if "Adiantamento salarial com IR" in desc:
            tipo = "provento"
        elif "Vale transporte" in desc or "INSS" in desc or "desconto" in desc.lower():
            tipo = "desconto"
        else:
            continue

        items.append({
            "codigo": match.group("codigo"),
            "descricao": desc,
            "tipo": tipo,
            "referencia": 0.0,
            "valor": br_to_float(match.group("valor")),
        })

    unique_items = []
    seen = set()
    for item in items:
        key = (item["codigo"], item["descricao"], item["tipo"], item["referencia"], item["valor"])
        if key not in seen:
            seen.add(key)
            unique_items.append(item)

    return unique_items


def parse_employee_block(block: str) -> dict:
    header = extract_employee_header(block)
    totals = extract_totals(block)
    items = extract_items(block)

    return {
        **header,
        **totals,
        "items": items,
        "raw_text": block,
    }


@router.post("/upload-payroll")
async def upload_payroll(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission Denied"
        )

    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Envie um arquivo PDF")

    os.makedirs("uploads", exist_ok=True)
    file_path = f"uploads/{file.filename}"

    content = await file.read()

    with open(file_path, "wb") as buffer:
        buffer.write(content)

    try:
        pdf = PdfReader(BytesIO(content))
    except Exception:
        raise HTTPException(status_code=400, detail="Não foi possível ler o PDF enviado")

    full_text_parts = []
    for page in pdf.pages:
        page_text = page.extract_text()
        if page_text:
            full_text_parts.append(page_text)

    if not full_text_parts:
        raise HTTPException(status_code=400, detail="O PDF não contém texto legível")

    full_text = "\n".join(full_text_parts)

    pdf_type = detect_pdf_type(full_text)
    mes_referencia, ano_referencia = parse_reference_from_text(full_text)
    advance_payment_date = parse_advance_payment_date(full_text)

    employee_blocks = split_employee_blocks(full_text)

    if not employee_blocks:
        raise HTTPException(
            status_code=400,
            detail="Não foi possível identificar os blocos de funcionários no PDF"
        )

    data_competencia = datetime(ano_referencia, mes_referencia, 1)
    ultimo_dia = monthrange(ano_referencia, mes_referencia)[1]
    data_vencimento = datetime(ano_referencia, mes_referencia, ultimo_dia)

    if pdf_type == "advance":
        data_pagamento = advance_payment_date
        observacao_base = f"Adiantamento importado do PDF referente a {mes_referencia:02d}/{ano_referencia}"
    else:
        data_pagamento = None
        observacao_base = f"Folha importada do PDF referente a {mes_referencia:02d}/{ano_referencia}"

    created = []
    skipped = []
    errors = []

    all_employees = db.query(accountModels.Employee).all()

    for block in employee_blocks:
        try:
            parsed = parse_employee_block(block)
            cpf_digits = only_digits(parsed.get("cpf"))

            if not cpf_digits:
                skipped.append({
                    "nome": parsed.get("nome"),
                    "motivo": "CPF não encontrado no PDF"
                })
                continue

            employee = db.query(accountModels.Employee).filter(
                accountModels.Employee.cpf == cpf_digits
            ).first()

            if not employee:
                for emp in all_employees:
                    if only_digits(emp.cpf) == cpf_digits:
                        employee = emp
                        break

            if not employee:
                skipped.append({
                    "nome": parsed.get("nome"),
                    "cpf": parsed.get("cpf"),
                    "motivo": "Funcionário não encontrado no banco pelo CPF"
                })
                continue

            existing = db.query(accountModels.EmployeePayroll).filter(
                accountModels.EmployeePayroll.employee_id == employee.id,
                accountModels.EmployeePayroll.company_id == employee.company_id,
                accountModels.EmployeePayroll.ano_referencia == ano_referencia,
                accountModels.EmployeePayroll.mes_referencia == mes_referencia,
                accountModels.EmployeePayroll.observacoes.ilike(f"%{observacao_base.split(' importado')[0]}%")
            ).first()

            if existing:
                skipped.append({
                    "employee_id": employee.id,
                    "nome": f"{employee.first_name or ''} {employee.last_name or ''}".strip(),
                    "cpf": employee.cpf,
                    "motivo": "Registro já cadastrado para este funcionário neste mês/ano e tipo de documento"
                })
                continue

            payroll = accountModels.EmployeePayroll(
                employee_id=employee.id,
                company_id=employee.company_id,
                ano_referencia=ano_referencia,
                mes_referencia=mes_referencia,
                data_competencia=data_competencia,
                data_vencimento=data_vencimento,
                data_pagamento=data_pagamento,
                salario_base=parsed.get("salario_base", 0),
                horas_mensais=parsed.get("horas_mensais", 0),
                base_inss=parsed.get("base_inss", 0),
                valor_inss=parsed.get("valor_inss", 0),
                base_fgts=parsed.get("base_fgts", 0),
                valor_fgts=parsed.get("valor_fgts", 0),
                base_irrf=parsed.get("base_irrf", 0),
                valor_irrf=parsed.get("valor_irrf", 0),
                base_rais=parsed.get("base_rais", 0),
                base_salario_familia=parsed.get("base_salario_familia", 0),
                total_proventos=parsed.get("total_proventos", 0),
                total_descontos=parsed.get("total_descontos", 0),
                salario_liquido=parsed.get("salario_liquido", 0),
                status="pago",
                paid=True,
                observacoes=observacao_base
            )

            for item in parsed.get("items", []):
                payroll.items.append(
                    accountModels.EmployeePayrollItem(
                        codigo=item.get("codigo"),
                        descricao=item.get("descricao"),
                        tipo=item.get("tipo"),
                        referencia=item.get("referencia", 0),
                        valor=item.get("valor", 0),
                    )
                )

            db.add(payroll)
            db.flush()

            result = db.query(accountModels.EmployeePayroll).options(
                joinedload(accountModels.EmployeePayroll.employee),
                joinedload(accountModels.EmployeePayroll.items)
            ).filter(
                accountModels.EmployeePayroll.id == payroll.id
            ).first()

            created.append({
                "payroll_id": result.id,
                "employee_id": employee.id,
                "nome": f"{employee.first_name or ''} {employee.last_name or ''}".strip(),
                "cpf": employee.cpf,
                "tipo_documento": pdf_type,
                "total_proventos": result.total_proventos,
                "total_descontos": result.total_descontos,
                "salario_liquido": result.salario_liquido,
                "base_irrf": result.base_irrf,
                "data_pagamento": result.data_pagamento,
                "items": [
                    {
                        "codigo": i.codigo,
                        "descricao": i.descricao,
                        "tipo": i.tipo,
                        "referencia": i.referencia,
                        "valor": i.valor
                    }
                    for i in result.items
                ]
            })

        except Exception as e:
            errors.append({
                "bloco": block[:300],
                "erro": str(e)
            })

    if created:
        db.commit()
    else:
        db.rollback()

    return {
        "arquivo": file.filename,
        "tipo_documento": pdf_type,
        "mes_referencia": mes_referencia,
        "ano_referencia": ano_referencia,
        "data_pagamento_adiantamento": advance_payment_date,
        "total_blocos_encontrados": len(employee_blocks),
        "total_criados": len(created),
        "total_pulados": len(skipped),
        "total_erros": len(errors),
        "created": created,
        "skipped": skipped,
        "errors": errors
    }