from .supplierSchemas import SupplierResponse, SupplierProductsResponse
from .productSchemas import ProductResponse
from .stockSchemas import AddressItemResponse, AddressProductsResponse

ProductResponse.model_rebuild(_types_namespace={"SupplierResponse": SupplierResponse})
SupplierProductsResponse.model_rebuild(_types_namespace={"ProductResponse": ProductResponse})
AddressItemResponse.model_rebuild(_types_namespace={"ProductResponse": ProductResponse})
AddressProductsResponse.model_rebuild(_types_namespace={"ProductResponse": ProductResponse})