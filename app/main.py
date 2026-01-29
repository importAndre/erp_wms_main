from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import engine, Base
from .server_config import SERVER_HOST

from app.routers.users import router as user_router
from app.routers.companies import router as company_router
from app.routers.products import router as product_router
from app.routers.compositions import router as comp_router
from app.routers.employees import router as employees_router
from app.routers.identificators import router as identifs_router
from app.routers.stock import router as stock_router
from app.routers.mercado_livre import router as ml_router
from app.routers.permissions import router as per_router

app = FastAPI()
Base.metadata.create_all(bind=engine)

origins = [SERVER_HOST[item] for item in SERVER_HOST]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

@app.get("/")
def hello():
    return {"message": "Welcome to the ultimate erp wms"}


app.include_router(user_router)
app.include_router(company_router)
app.include_router(product_router)
app.include_router(comp_router)
app.include_router(employees_router)
app.include_router(identifs_router)
app.include_router(stock_router)
app.include_router(ml_router)
app.include_router(per_router)
