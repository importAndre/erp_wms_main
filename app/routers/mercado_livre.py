import datetime
from fastapi import APIRouter, Depends
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
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = userServices.User(user=current_user, db=db)
    url = f'{API_URL}/mercado-livre/listings'

    companies = user.get_companies()
    result = {}
    for c in companies:
        params = {
            "company_id": c.id
        }
        req = requests.get(url=url, params=params)
        if req.status_code == 200:
            result[c.nome_fantasia] = req.json()

    return result
    


@router.get("/listing/{listing}", response_model=mercadoLivreSchemas.MercadoLivreListing)
def get_listing(
    listing: str,
    company_id: int
) -> mercadoLivreSchemas.MercadoLivreListing:
    lis = mercadoLivreServices.MercadoLivreListing(listing=listing, cid=company_id)
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
    current_user=Depends(get_current_user)
):
    url = f'{API_URL}/mercado-livre/infos/'
    body = {
        "company_id": company_id,
        "date_begin": date_begin,
        "date_end": date_end
    }

    req = requests.post(url=url, json=body)
    if req.status_code == 200:
        return req.json()
