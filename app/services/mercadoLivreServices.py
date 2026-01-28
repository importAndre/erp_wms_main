from ..schemas import mercadoLivreSchemas
from sqlalchemy.orm import Session
from ..database import get_db
from fastapi import Depends
from typing import Optional
from .userServices import User
import requests
from ..server_config import API_URL

class Account:
    def __init__(
        self,
        cid: int = None,
        ):
        self.cid = cid
        self.account = None
        # self._load_account()


    def _load_account(self):
        url = f"{API_URL}/mercado-livre/client/me"
        params = {"company_id": self.cid}
        req = requests.get(url=url, params=params)
        if req.status_code == 200:
            # return req.json()
            self.account = mercadoLivreSchemas.MercadoLivreUser.model_validate(req.json())

    def get_account(self) -> mercadoLivreSchemas.MercadoLivreUser:
        if not self.account:
            self._load_account()
        return self.account



class MercadoLivreListing:
    def __init__(
            self,
            listing: str,
            cid: Optional[int] = None
            ):
        self.listing_id = listing if "MLB" in listing.upper() else f"MLB{listing}"
        self.cid = cid
        self.listing = None

    
    def _load_listing(self, refresh=False):
        url = f'{API_URL}/mercado-livre/listings/{self.listing_id}'
        params = {
            "company_id": self.cid,
            "prices": True,
            "stock": True
        }

        req = requests.get(url=url, params=params)
        if req.status_code == 200:
            self.listing = mercadoLivreSchemas.MercadoLivreListing.model_validate(req.json())
            self.listing.prices.discount_percentage = 1 - (self.listing.prices.amount / self.listing.listings[0].base_price)

    def get_listing(self):
        if not self.listing:
            self._load_listing()
        return self.listing


class MercadoLivreOrder:
    def __init__(
        self,
        order_id: str,
        cid: int
        ):
        self.order_id = order_id
        self.cid = cid
        self.order = None

    def _load_order(self):
        url = f'{API_URL}/mercado-livre/orders/{self.order_id}'
        params = {
            "company_id": self.cid,
            "shipment": True
        }

        req = requests.get(url=url, params=params)
        if req.status_code == 200:
            data = req.json()

            if isinstance(data, list):
                orders = []
                for o in data:
                    orders.append(mercadoLivreSchemas.MercadoLivreOrder.model_validate(o))
                self.order = orders

            elif isinstance(data, dict):
                self.order = mercadoLivreSchemas.MercadoLivreOrder.model_validate(data)
    
    def get_order(self):
        if not self.order:
            self._load_order()
        return self.order