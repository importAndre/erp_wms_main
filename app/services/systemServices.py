import pandas as pd
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..models import identificatorsModels, productModels, suppliersModels
from ..schemas import finantialsSchemas
from ..database import get_db, SessionLocal
import requests
from ..server_config import API_URL


router = APIRouter(
    prefix="/services/system",
    tags=["System"],
    responses={404: {"description": "Not found"}},
)


@router.get("/check-products")
def check_products_update(
    db: Session = Depends(get_db)
):
    db = SessionLocal()
    identifs = db.query(identificatorsModels.Identificators).filter(
        identificatorsModels.Identificators.identif_type == 'supplier_code'
    ).all()
    url = f"{API_URL}/invoices/product"
    orphan_identificators = []
    products_updated = []
    products_to_update = []
    verification_errors = []

    product_ids = {i.product_id for i in identifs if i.product_id}
    products = db.query(productModels.Product).filter(
        productModels.Product.id.in_(product_ids)
    ).all() if product_ids else []
    products_by_id = {product.id: product for product in products}

    identifs_by_product = {}
    for identif in identifs:
        if not identif.product_id or identif.product_id not in products_by_id:
            orphan_identificators.append(identif.id)
            continue
        identifs_by_product.setdefault(identif.product_id, []).append(identif)

    supplier_ids = {product.supplier_id for product in products if product.supplier_id}
    suppliers = db.query(suppliersModels.Suppliers).filter(
        suppliersModels.Suppliers.id.in_(supplier_ids)
    ).all() if supplier_ids else []
    suppliers_by_id = {supplier.id: supplier for supplier in suppliers}

    for product_id, product_identifs in identifs_by_product.items():
        product = products_by_id[product_id]
        supplier = suppliers_by_id.get(product.supplier_id)
        if not supplier or not supplier.cnpj:
            verification_errors.append({
                "product_id": product.id,
                "sku": product.sku,
                "error": "Fornecedor sem CNPJ cadastrado"
            })
            continue

        last_history = db.query(productModels.ProductHistoricalPrices).filter(
            productModels.ProductHistoricalPrices.product_id == product.id
        ).order_by(
            productModels.ProductHistoricalPrices.created_at.desc()
        ).first()
        last_update = last_history.created_at if last_history else None

        newest_entry = None
        for identif in product_identifs:
            params = {
                "cprod": {identif.value},
                "supplier_cnpj": supplier.cnpj
            }

            try:
                req = requests.get(url=url, params=params, timeout=30)
                req.raise_for_status()
                data = req.json()
            except (requests.RequestException, ValueError) as exc:
                verification_errors.append({
                    "product_id": product.id,
                    "sku": product.sku,
                    "identificator_id": identif.id,
                    "identificator": identif.value,
                    "error": str(exc)
                })
                continue

            if not data or not data.get("invoice"):
                continue

            invoice = finantialsSchemas.InvoiceBase.model_validate(data["invoice"])
            if not invoice.dh_emissao:
                continue

            if not newest_entry or invoice.dh_emissao > newest_entry["date"]:
                newest_entry = {
                    "date": invoice.dh_emissao,
                    "invoice_number": invoice.numero,
                    "identificator_id": identif.id,
                    "identificator": identif.value
                }

        result = {
            "product_id": product.id,
            "sku": product.sku,
            "last_update": last_update,
            "latest_entry": newest_entry["date"] if newest_entry else None,
            "invoice_number": newest_entry["invoice_number"] if newest_entry else None,
            "identificator_id": newest_entry["identificator_id"] if newest_entry else None,
            "identificator": newest_entry["identificator"] if newest_entry else None,
            "identificators_checked": len(product_identifs)
        }

        if newest_entry and (not last_update or newest_entry["date"] > last_update):
            products_to_update.append(result)
        else:
            products_updated.append(result)

    df = pd.DataFrame(columns=['pid'], data=[i['product_id'] for i in products_to_update])
    df.to_csv("products_to_update.csv")
    db.close()
    return {
        "products_updated": products_updated,
        "products_to_update": products_to_update,
        "total_products_updated": len(products_updated),
        "total_products_to_update": len(products_to_update),
        "orphan_identificators": orphan_identificators,
        "total_orphan_identificators": len(orphan_identificators),
        "verification_errors": verification_errors
    }



@router.get("/stock")
def check_stock_update():
    pass