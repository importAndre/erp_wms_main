import datetime
from fastapi import APIRouter, Depends, HTTPException
from ..schemas import mercadoLivreSchemas
from ..oauth2 import get_current_user
from ..server_config import API_URL
import requests
from typing import Optional, Union, List
from ..services import userServices, mercadoLivreServices, productServices
from sqlalchemy.orm import Session
from ..database import get_db
from ..services import mercadoLivreServices
from copy import deepcopy

router = APIRouter(
    prefix="/mercado-livre",
    tags=["Mercado Livre"]
)


@router.post("/register")
def register_client(
    client: mercadoLivreSchemas.MercadoLivreRegisterClient,
    current_user=Depends(get_current_user)
):
    
    req = requests.post(
        url=f"{API_URL}/mercado-livre/client/register",
        json=client.__dict__
        )
    
    if req.status_code == 200:
        return req.json()


@router.get("/me", response_model=mercadoLivreSchemas.MercadoLivreUser)
def get_account(
    company_id: Optional[int] = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
) -> mercadoLivreSchemas.MercadoLivreUser:
    
    if not company_id:
        return {"message": "Not implemented yet, please inform company_id"}

    acc = mercadoLivreServices.Account(cid=company_id)
    return acc.get_account()


@router.get("/listings")
def get_listings(
    offset: int = 0,
    limit: int = 100,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = userServices.User(user=current_user, db=db)
    url = f'{API_URL}/mercado-livre/listings'

    companies = user.get_companies()
    result = {}
    for c in companies:
        params = {
            "company_id": c.id,
            "desc": False,
            "offset": offset,
            "limit": limit
        }
        req = requests.get(url=url, params=params)
        if req.status_code == 200:
            result[c.nome_fantasia] = req.json()

    return result
    


@router.get("/listing/{listing}", response_model=mercadoLivreSchemas.MercadoLivreListingResponse)
def get_listing(
    listing: str,
    company_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
) -> mercadoLivreSchemas.MercadoLivreListingResponse:
    lis = mercadoLivreServices.MercadoLivreListing(listing=listing, cid=company_id, db=db, current_user=current_user)
    return lis.get_listing()
    
    
@router.get("/order/{order_id}", response_model=Union[mercadoLivreSchemas.MercadoLivreOrder, List[mercadoLivreSchemas.MercadoLivreOrder]])
def get_order(
    order_id: str,
    company_id: int
) -> Union[mercadoLivreSchemas.MercadoLivreOrder, List[mercadoLivreSchemas.MercadoLivreOrder]]:
    order = mercadoLivreServices.MercadoLivreOrder(order_id=order_id, cid=company_id)
    return order.get_order()

@router.get("/orders", response_model=List[mercadoLivreSchemas.MercadoLivreOrder])
def get_orders(
    # filters: Optional[mercadoLivreSchemas.MercadoLivreOrdersRequest] = None,
    company_id: int,
    date_begin: Optional[str] = None,
    date_end: Optional[str] = None,
    current_user=Depends(get_current_user)
) -> List[mercadoLivreSchemas.MercadoLivreOrder]:
    url = f'{API_URL}/mercado-livre/orders/'
    body = {
        "company_id": company_id,
        "date_begin": date_begin,
        "date_end": date_end
    }

    req = requests.post(url=url, json=body)
    if req.status_code == 200:
        data = req.json()
        # return data
        return [mercadoLivreSchemas.MercadoLivreOrder.model_validate(d) for d in data]
    


@router.get("/infos")
def get_infos(
    company_id: int,
    date_begin: Optional[str] = None,
    date_end: Optional[str] = None,
    listing_id: Optional[str] = None,
    current_user=Depends(get_current_user)
):
    url = f'{API_URL}/mercado-livre/infos/'
    body = {
        "company_id": company_id,
        "date_begin": date_begin,
        "date_end": date_end,
        "listing_id": listing_id
    }
    print(body)

    req = requests.post(url=url, json=body)
    if req.status_code == 200:
        return req.json()


@router.post("/calculate")
def calculate_listing(
    changes: mercadoLivreSchemas.CalculateListing,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):

    listing_obj = mercadoLivreServices.MercadoLivreListing(
        listing=changes.listing,
        db=db,
        current_user=current_user,
        cid=changes.company_id
    )
    listing_infos = listing_obj.get_listing()

    result = {
        "current": {},
        "new": {}
    }

    products_by_sku = {item.sku: item for item in listing_infos.items}
    found_sku = False

    for listing in listing_infos.listing.listings:
        if changes.sku and listing.sku != changes.sku:
            continue

        found_sku = True

        prod = products_by_sku.get(listing.sku)
        if not prod:
            continue

        # cópia do estado atual
        current_listing = deepcopy(listing)

        result["current"][prod.sku] = create_listing_dict(
            listing=current_listing,
            product=prod
        )

        # outra cópia para simulação
        new_listing = deepcopy(listing)

        if changes.price is None:
            changes.price = listing.price

        new_taxes = calculate_new_taxes(
            price=changes.price,
            listing=new_listing.listing_id,
            sku=prod.sku,
            company_id=prod.company_id
        )

        new_listing.price = changes.price
        new_listing.base_price = changes.price
        new_listing.percentage_discount = new_taxes["percentage_discount"]
        new_listing.percentage_fee = new_taxes["percentage_fee"]
        new_listing.fixed_fee = new_taxes["new_fixed"]
        new_listing.liq_revenue = (
            new_listing.price
            - new_listing.fixed_fee
            - new_listing.percentage_discount
        )

        if changes.price >= 79:
            new_listing.free_shipping = True
            new_listing.liq_revenue -= new_listing.freight_cost
        else:
            new_listing.free_shipping = False

        result["new"][prod.sku] = create_listing_dict(
            listing=new_listing,
            product=prod
        )

    if changes.sku and not found_sku:
        raise HTTPException(
            status_code=404,
            detail=f"SKU {changes.sku} não encontrado no listing {changes.listing}"
        )

    return result


def create_listing_dict(listing, product):
    result = {
        "price": listing.price,
        "base_price": listing.base_price,
        # "original_price": listing.original_price,
        "logistic_type": listing.logistic_type,
        "sku": listing.sku,
        "package_weight": listing.package_weight,
        "weight_unit": listing.weight_unit,
        "free_shipping": listing.free_shipping,
        "freight_cost": listing.freight_cost,
        "percentage_discount": listing.percentage_discount,
        "percentage_fee": listing.percentage_fee,
        "liq_revenue": listing.liq_revenue,
        "fixed_fee": listing.fixed_fee,
        "flex_fee": listing.flex_fee,
        "cmv": product.price_after_taxes
    }
    result = calculate_taxes(price=listing.price, revenue=listing.liq_revenue, cmv=product.price_after_taxes, dict_to_update=result)
    return result




def calculate_taxes(price, revenue, cmv, dict_to_update):
    icms_saida = price * 18 / 100
    pis_saida = (price - icms_saida) * 1.65 / 100
    cofins_saida = (price - icms_saida) * 7.6 / 100
    gross = revenue - cmv
    profit = gross - icms_saida - pis_saida - cofins_saida
    dict_to_update["icms_saida"] = icms_saida
    dict_to_update["pis_saida"] = pis_saida
    dict_to_update["cofins_saida"] = cofins_saida
    dict_to_update["gross"] = gross
    dict_to_update["profit"] = profit
    return dict_to_update


def calculate_new_taxes(price: float, listing: str, sku: str, company_id: int):
    url = f"{API_URL}/mercado-livre/listings/simulate-price"
    params = {
        "price": price,
        "listing": listing,
        "sku": sku,
        "company_id": company_id
    }
    req = requests.post(url=url, json=params)
    if req.status_code == 200:
        data = req.json()
        return data