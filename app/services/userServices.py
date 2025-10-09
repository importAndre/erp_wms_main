from ..models.accountModels import User as UserModel, Employee
from sqlalchemy.orm import Session
from ..database import get_db
from fastapi import Depends

class User:
    def __init__(self, user: UserModel, db: Session = Depends(get_db)):
        self._user = user
        self.db = db
        self.employee = None

    def __getattr__(self, username):
        return getattr(self._user, username)

    def get_user(self):
        return self._user

    def get_employee(self):
        e = self.db.query(Employee).filter(Employee.user_id == self._user.id).first()
        if not self._user.employee_id and e:
            self._user.employee_id = e.id
            self._user.is_employee = True
        self.employee = e
        return self.employee
