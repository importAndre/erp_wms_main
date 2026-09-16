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
from app.routers.suppliers import router as sup_router
from app.routers.finantials import router as fin_router
from app.services.systemServices import router as sys_router
from app.routers.orders import router as order_router

from apscheduler.schedulers.background import BackgroundScheduler


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


from app.services.systemServices import check_products_update
from app.routers.orders import get_ml_orders
def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_products_update, 'interval', minutes=30)
    scheduler.add_job(get_ml_orders, 'interval', minutes=5)
    scheduler.start()

start_scheduler()

app.include_router(user_router)
app.include_router(company_router)
app.include_router(product_router)
app.include_router(comp_router)
app.include_router(employees_router)
app.include_router(identifs_router)
app.include_router(stock_router)
app.include_router(ml_router)
app.include_router(per_router)
app.include_router(sup_router)
app.include_router(fin_router)
app.include_router(sys_router)
app.include_router(order_router)
