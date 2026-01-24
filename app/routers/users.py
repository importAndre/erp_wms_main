from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..models import accountModels
from ..schemas import userSchemas
from ..database import get_db
from .. import utils, oauth2
from ..oauth2 import get_current_user
from ..services import userServices

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

@router.post("/create", status_code=status.HTTP_201_CREATED, response_model=userSchemas.UserResponse)
def create_user(
    user: userSchemas.UserCreate, 
    db: Session = Depends(get_db)
    ):
    db_user = db.query(accountModels.User).filter(accountModels.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    
    hashed_password = utils.get_password_hash(user.password)

    new_user = accountModels.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        is_active=True,
        is_superuser=user.is_superuser,
        is_employee=True if user.is_employee else False,
        employee_id=user.employee_id
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return userServices.User(user_id=new_user.id, db=db).get_user()


@router.post("/login", response_model=userSchemas.Token)
def login(
        user_credentials: userSchemas.UserLogin, 
        db: Session = Depends(get_db)
        ):
    user = db.query(accountModels.User).filter(accountModels.User.email == user_credentials.email).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials")

    if not utils.verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials")
    
    if user.is_active == False:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive")

    access_token = oauth2.create_access_token(data={"user_id": user.id})

    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me")
def get_user_me(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return userServices.User(user=current_user, db=db).get_user()
    


@router.get("/main")
def load_main_page(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = userServices.User(user=current_user, db=db)
    if user.get_user().is_superuser:
        return load_super_user_main_page(user=user, db=db, current_user=current_user)




def load_super_user_main_page(
    user: userServices.User,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # from .mercado_livre import get_infos
    
    # infos = {}
    # for c in user.get_companies():
    #     infos[c.nome_fantasia] = get_infos(
    #         company_id=c.id,
    #         date_begin="2026-01-01",
    #         current_user=user
    #     )

    # return infos
    return userSchemas.SuperUserMainPage()


def load_user_main_page(
    user: userServices.User,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return userSchemas.UserMainPage()