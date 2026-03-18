from ..schemas import mercadoLivreSchemas
from sqlalchemy.orm import Session
from ..database import get_db
from fastapi import Depends
from typing import Optional
from .userServices import User
import requests
from ..server_config import API_URL
from ..routers.products import search_by_sku
from ..oauth2 import get_current_user


loaded_listings = {}

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
            cid: Optional[int] = None,
            db: Session = Depends(get_db),
            current_user=Depends(get_current_user),
            ):
        self.listing_id = listing if "MLB" in listing.upper() else f"MLB{listing}"
        self.cid = cid
        self.listing = None
        self.listing_product = []
        self.db = db
        self.current_user = current_user

    
    def _load_listing(self, refresh=False):
        url = f'{API_URL}/mercado-livre/listings/{self.listing_id}'
        params = {
            "company_id": self.cid,
            "prices": True,
            "stock": True
        }

        if self.listing_id in loaded_listings and not refresh:
            self.listing = loaded_listings[self.listing_id]
            self.listing_product = []
            self._get_product()
            return

        req = requests.get(url=url, params=params)
        if req.status_code == 200:
            self.listing = mercadoLivreSchemas.MercadoLivreListing.model_validate(req.json())

            try:
                self.listing.prices.discount_percentage = 1 - (
                    self.listing.prices.amount / self.listing.listings[0].base_price
                )
            except TypeError as e:
                print("Discount percentage not working: ", e)

            loaded_listings[self.listing_id] = self.listing

            self.listing_product = []
            self._get_product()

    def get_listing(self, refresh=False):
        if not self.listing or refresh:
            self._load_listing(refresh=refresh)

        return mercadoLivreSchemas.MercadoLivreListingResponse(
            listing=self.listing,
            items=self.listing_product
        )
        
    def _get_product(self):
        self.listing_product = []
        for lis in self.listing.listings:
            self.listing_product.append(
                search_by_sku(
                    sku=lis.sku,
                    db=self.db,
                    current_user=self.current_user
                )
            )

    def simulate_taxes(self, new_price):
        url = f'{API_URL}/mercado-livre/listings/new-tax-sim/{self.listing_id}'
        params = {
            "lis": self.listing_id,
            "price": new_price
        }

        req = requests.get(url=url, params=params)
        return req.json()



    # def get_listings_finantials(self):


    




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