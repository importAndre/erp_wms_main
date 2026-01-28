from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class MercadoLivreRegisterClient(BaseModel):
    company_id: int
    client_id: str
    client_secret: str


class MercadoLivreOrdersRequest(BaseModel):
    company_id: int
    # company_id: Optional[int] = None
    date_begin: Optional[datetime] = None
    date_end: Optional[datetime] = None


class MercadoLivreUser(BaseModel):

    class AddressInfos(BaseModel):
        address: Optional[str] = None
        city: Optional[str] = None
        state: Optional[str] = None
        zip_code: Optional[str] = None

    class SellerReputation(BaseModel):

        class TransactionInfos(BaseModel):

            class RatingsInfos(BaseModel):
                negative: Optional[float] = None
                neutral: Optional[float] = None
                positive: Optional[float] = None
            
            canceled:Optional[int] = None
            completed: Optional[int] = None
            period:Optional[str] = None
            ratings:Optional[RatingsInfos] = None


        class MetricsInfos(BaseModel):
            
            class MetricsBase(BaseModel):
                period: Optional[str] = None
                completed: Optional[int] = None
                rate: Optional[float] = None
                value: Optional[int] = None

            sales: Optional[MetricsBase] = None
            claims: Optional[MetricsBase] = None
            delayed_handling_time: Optional[MetricsBase] = None
            cancellations: Optional[MetricsBase] = None
        
        level_id: Optional[str] = None
        power_seller_reputation: Optional[str] = None
        transactions: Optional[TransactionInfos] = None
        metrics: Optional[MetricsInfos] = None

    class StatusInfos(BaseModel):
        mercadoenvios: Optional[str] = None

    class CreditInfos(BaseModel):
        consumed: Optional[float] = None
        credit_level_id: Optional[str] = None
        rank: Optional[str] = None

    class ThumbnailInfo(BaseModel):
        picture_url: Optional[str] = None

    nickname: Optional[str] = None
    registration_date: Optional[str] = None
    first_name: Optional[str] = None
    email: Optional[str] = None
    address: Optional[AddressInfos] = None
    points: Optional[int] = None
    permalink: Optional[str] = None
    seller_experience: Optional[str] = None
    seller_reputation: Optional[SellerReputation] = None
    status: Optional[StatusInfos] = None
    # mercado_envios: Optional[str] = None
    credit: Optional[CreditInfos] = None
    thumbnail: Optional[ThumbnailInfo] = None


class MercadoLivreListing(BaseModel):

    class PricesInfos(BaseModel):
        amount: Optional[float] = None
        start_time: Optional[str] = None
        type: Optional[str] = None
        last_updated: Optional[str] = None
        end_time: Optional[str] = None
        promotion_type: Optional[str] = None
        discount_percentage: Optional[float] = None

    class Stocks(BaseModel):
        created_at: Optional[str] = None
        selling_address: Optional[int] = None
        meli_facility: Optional[int] = None
        stock_id: Optional[str] = None


    class ListingInfo(BaseModel):

        class PicturesInfos(BaseModel):
            url: Optional[str] = None
            size: Optional[str] = None

        price: Optional[float] = None
        start_time: Optional[str] = None
        listing_id: Optional[str] = None
        base_price: Optional[float] = None
        logistic_type: Optional[str] = None
        shipping_tags: Optional[List[str]] = None
        health: Optional[float] = None
        title: Optional[str] = None
        available_quantity: Optional[int] = None
        permalink: Optional[str] = None
        sku: Optional[str] = None
        sold_quantity: Optional[int] = None
        inventory_id: Optional[str] = None
        description: Optional[str] = None
        user_product_id: Optional[str] = None
        thumbnail: Optional[str] = None
        status: Optional[str] = None
        pictures: Optional[List[PicturesInfos]] = None


    listings: Optional[List[ListingInfo]] = None
    prices: Optional[PricesInfos] = None
    stock: Optional[List[Stocks]] = None


class MercadoLivreOrder(BaseModel):
    order_id: Optional[str] = None
    listing_id: Optional[str] = None
    status: Optional[str] = None
    total_received: Optional[float] = None
    pack_id: Optional[str] = None
    sku: Optional[str] = None
    substatus: Optional[str] = None
    ads: Optional[bool] = None
    client_nickname: Optional[str] = None
    quantity: Optional[int] = None
    logistic_type: Optional[str] = None
    mediation_id: Optional[int] = None
    client_name: Optional[str] = None
    unit_price: Optional[float] = None
    tracking_number: Optional[str] = None
    shipping_cost: Optional[float] = None
    full_unit_price: Optional[float] = None
    shipping_received: Optional[float] = None
    total_amount: Optional[float] = None
    sale_fee: Optional[float] = None
    shipping_limit: Optional[str] = None
    paid_amount: Optional[float] = None
    payment_method_id: Optional[str] = None
    shipping_status: Optional[str] = None
    date_created: Optional[str] = None
    installments: Optional[int] = None