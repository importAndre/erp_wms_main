from fastapi import APIRouter


router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}}
)

@router.get("/")
def read_root():
    return {"message": "Welcome to the users router"}

@router.post("/create", response_model=accountsSchemas.Account)
def create_account(account: accountsSchemas.AccountCreate, db: Session = Depends(get_db)):
    query = db.query(accountModels.Account).filter(accountModels.Account.email == account.email).first()
    if query: 
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    hashed_password = utils.get_password_hash(account.password)
    account.password = hashed_password
    db_account = accountModels.Account(email=account.email, username=account.username, password=account.password)
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account