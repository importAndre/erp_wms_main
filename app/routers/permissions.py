from typing import Optional
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

}

@router.get("/{per}")
def get_per(
    per: Optional[str] = None
):
    global pers
    if per in pers:
        return pers[per]
    return pers

@router.get("/router/{router}")
def search_by_router(
    router: Optional[str] = None
):
    global pers
    result = {}
    for item in pers:
        for i in pers[item]:
            if i not in result:
                result[i] = {
                    "routers": pers[item][i],
                    "permissions": [item]
                }
            if i in result:
                result[i]["routers"].extend(pers[item][i])
                result[i]["permissions"].append(item)


    return result[f"/{router}"] if router else result