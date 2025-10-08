from ..models.accountModels import User, Employee
from sqlalchemy.orm import Session
from ..database import get_db
from fastapi import Depends

class User:

    def __init__(
        self,
        user: User,
        db: Session = Depends(get_db)
        ):
        self.user = user


    def get_user(self):
        return self.user
    
    def get_employee(self):
        e = self.db.query(Employee).filter(Employee.user_id == self.user.id).first()
        if not self.user.employee_id:
            self.user.employee_id = e.id
            self.user.is_employee = True
        self.employee = e
        return self.employee