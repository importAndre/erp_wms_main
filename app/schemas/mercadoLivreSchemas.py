from pydantic import BaseModel

class MercadoLivreRegisterClient(BaseModel):
    company_id: int
    client_id: str
    client_secret: str