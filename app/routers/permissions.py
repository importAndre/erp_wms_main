from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter(
    prefix="/permissions",
    tags=["permissions"],
    responses={404: {"description": "Not found"}},
)

pers = {
    "alter_permission": {
        "/users": ["/permission"],
    },
    "edit_product": {
        "/products": ["/edit"],
    },
    "create_product": {
        "/products": ["/create"],
    },
    "create_supplier": {
        "/suppliers": ["/create"],
    },



    "create_product": "/products/create",
    "create_supplier": "/suppliers/create"
}

@router.get("/")
def get_per():
    global pers
    return pers