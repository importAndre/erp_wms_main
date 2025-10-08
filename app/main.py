from fastapi import FastAPI
from .database import engine, Base

from app.routers.users import router as user_router
from app.routers.companies import router as company_router

app = FastAPI()
Base.metadata.create_all(bind=engine)

@app.get("/")
def hello():
    return {"message": "Welcome to the ultimate erp wms"}


app.include_router(user_router)
app.include_router(company_router)
