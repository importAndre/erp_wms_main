import datetime
from fastapi import APIRouter, Depends, UploadFile, File
from ..schemas import mercadoLivreSchemas
from ..oauth2 import get_current_user
from ..server_config import API_URL
import requests
from typing import Optional, Union, List
from ..services import userServices, mercadoLivreServices
from sqlalchemy.orm import Session
from ..database import get_db
from ..services import mercadoLivreServices


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
