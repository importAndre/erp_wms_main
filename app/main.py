from fastapi import FastAPI
from models.database import Base, engine

from .routers import (
    user
)

app = FastAPI()
Base.metadata.create_all(bind=engine)



@app.get("/")
def hello():
    return {"message": "Welcome to the ultimate erp wms"}


app.include_router(router=user.router)