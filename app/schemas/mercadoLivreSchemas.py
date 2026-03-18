from datetime import datetime
from typing import Optional, List, Union
from pydantic import BaseModel
from .productSchemas import ProductResponse
from .compositionSchemas import CompositionResponse

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

    class TaxesInfos(BaseModel):
        class FeeDetails(BaseModel):
            fixed_fee: Optional[float] = None
            gross_amount: Optional[float] = None
            percentage_fee: Optional[float] = None

        currency_id: Optional[str ] = None
        free_relist: Optional[bool] = None
        listing_exposure: Optional[str] = None
        listing_fee_amount: Optional[float] = None
        listing_fee_details: Optional[FeeDetails] = None
        listing_type_id: Optional[str] = None
        listing_type_name: Optional[str] = None
        requires_picture: Optional[bool] = None
        sale_fee_amount: Optional[float] = None
        sale_fee_details: Optional[FeeDetails] = None
        stop_time: Optional[datetime] = None

    class FreightInfos(BaseModel):

        class Coverage(BaseModel):
            class CountryInfos(BaseModel):
                class DiscountInfos(BaseModel):
                    rate: Optional[float] = None
                    type: Optional[str] = None
                    promoted_amount: Optional[float] = None

                list_cost: Optional[float] = None
                currency_id: Optional[str] = None
                billable_weight: Optional[float] = None
                discount: Optional[DiscountInfos] = None

            all_country: Optional[CountryInfos]
        
        coverage: Optional[Coverage] = None


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
        package_height: Optional[float] = None
        package_length: Optional[float] = None
        package_width: Optional[float] = None
        package_weight: Optional[float] = None
        measurements_unit: Optional[str] = None
        weight_unit: Optional[str] = None
        free_shipping: Optional[bool] = None
        freight_cost: Optional[float] = None
        percentage_discount: Optional[float] = None
        percentage_fee: Optional[float] = None
        fixed_fee: Optional[float] = None
        flex_fee: Optional[float] = None
        fixed_fee: Optional[float] = None
        flex_fee: Optional[float] = None
        liq_revenue: Optional[float] = None


    listings: Optional[List[ListingInfo]] = None
    taxes: Optional[TaxesInfos] = None
    freight: Optional[FreightInfos] = None
    prices: Optional[PricesInfos] = None
    stock: Optional[List[Stocks]] = None
    new_taxes: Optional[float] = None


class MercadoLivreListingResponse(BaseModel):
    listing: Optional[MercadoLivreListing] = None
    items: Optional[List[Union[CompositionResponse, ProductResponse]]] = None


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




class CalculateListing(BaseModel):
    listing: str
    company_id: int
    price: Optional[float] = None
    sku: Optional[str] = None
    # desired_margin: Optional[float] = None