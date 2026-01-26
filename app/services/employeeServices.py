from ..models.accountModels import Employee as EmployeeModel
from ..schemas import employeesSchemas
from sqlalchemy.orm import Session
from ..database import get_db
from fastapi import Depends
from typing import Optional
from .userServices import User


class Employee:

    def __init__(
        self,
        emp_id: Optional[int] = None,
        emp: Optional[EmployeeModel] = None,
        db: Session = Depends(get_db)
        ):
        self.emp_id = emp_id if emp_id else emp.id
        self.id = None
        self.first_name = None
        self.last_name = None
        self.email = None
        self.phone_number = None
        self.position = None
        self.department = None
        self.hire_date = None
        self.salary = None
        self.is_active = None
        self.company_id = None
        self.user_id = None
        

    def _load_employee(self):
        if not self.emp_id:
            raise ValueError("Please inform employee id (eid)")

        query = self.db.query(EmployeeModel).filter(EmployeeModel.id == self.emp_id).first()
        if query:
            for column in EmployeeModel.__table__.columns:
                setattr(self, column.name, getattr(query, column.name))

    def get_employee(self, refresh=False):
        if refresh:
            self._load_employee()
        return employeesSchemas.EmployeeResponse(
            first_name=self.first_name,
            last_name=self.last_name,
            email=self.email,
            phone_number=self.phone_number,
            position=self.position,
            department=self.department,
            hire_date=self.hire_date,
            salary=self.salary,
            is_active=self.is_active,
            company_id=self.company_id,
            user_id=self.user_id,
            id=self.emp_id
        )
