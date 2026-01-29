# from ..models.accountModels import User as UserModel, Employee, Company as CompanyModel
from ..models import accountModels
from sqlalchemy.orm import Session
from ..database import get_db
from fastapi import Depends
from typing import Optional, List
from ..schemas import userSchemas
from ..services.companyServices import Company
from fastapi import HTTPException, status


class User:
    def __init__(
            self, 
            user: Optional[accountModels.User] = None, 
            user_id: Optional[int] = None, 
            db: Session = Depends(get_db)
            ):
        self._user = user
        self.db = db
        self.employee = None
        self._preferences = None 
        self.user_id = user_id
        self.permissions = []
        self._load_user()
        self.companies = None

    def __getattr__(self, username):
        return getattr(self._user, username)
    
    def _load_user(self):
        if self._user:
            if len(self.permissions) == 0:
                self._load_permissions()
            return
        query = self.db.query(accountModels.User).filter(accountModels.User.id == self.user_id).first()
        if not query:
            raise AttributeError("User not found")
        self._user = query
        self._load_permissions()

    def get_user(self):
        return userSchemas.UserResponse(
            id=self._user.id,
            username=self._user.username,
            email=self._user.email,
            is_superuser=self._user.is_superuser,
            employee_id=self._user.employee_id,
            is_active=self._user.is_active,
            is_employee=self._user.is_employee,
            permissions=self.permissions
        )

    def get_employee(self):
        e = self.db.query(accountModels.Employee).filter(accountModels.Employee.user_id == self._user.id).first()
        if not self._user.employee_id and e:
            self._user.employee_id = e.id
            self._user.is_employee = True
        self.employee = e
        return self.employee
    
    def get_companies(self):
        if self.companies:
            return self.companies
        query = self.db.query(accountModels.CompanyModel).all()
        self.companies = [Company(company_id=item.id, db=self.db).get_company() for item in query]
        return self.companies
    
    def _load_permissions(self):
        if self._user.is_superuser:
            self.permissions = ["all"]
        query = self.db.query(accountModels.UserPersmissions).filter(accountModels.UserPersmissions.user_id == self.user_id).first()
        if query:
            self.permissions = query.permissions

    def check_users_permission(self, task: str):
        if task in self.permissions or self._user.is_superuser:
            return True
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Permission: {task} not allowed.")


    

        