from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..models.accountModels import Employee
from ..schemas import employeesSchemas
from ..services import employeeServices
from ..database import get_db
from ..oauth2 import get_current_user
from typing import Union, List, Optional

router = APIRouter(
    prefix="/employees",
    tags=["employees"],
    responses={404: {"description": "Not found"}},
)

@router.get("/")
def get_employees(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission Denied")
    return db.query(Employee).all()


@router.post("/register")
def register_employee(
    employee: employeesSchemas.EmployeeRegister,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    
    new_employee = Employee(
        first_name=employee.first_name,
        last_name=employee.last_name,
        email=employee.email,
        phone_number=employee.phone_number,
        position=employee.position,
        department=employee.department,
        hire_date=employee.hire_date,
        salary=employee.salary,
        is_active=employee.is_active,
        company_id=employee.company_id,
        user_id=employee.user_id
    )
    db.add(new_employee)
    db.commit()
    db.refresh(new_employee)

    return new_employee

@router.get("/search/{emp_id}", response_model=Union[employeesSchemas.EmployeeResponse, List[employeesSchemas.EmployeeResponse]])
def get_employee(
    emp_id: Optional[int] = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Union[employeesSchemas.EmployeeResponse, List[employeesSchemas.EmployeeResponse]]:

    if not emp_id:
        employees = db.query(Employee).all()
        return [employeeServices.Employee(emp_id=emp.id, db=db).get_employee() for emp in employees]
    return employeeServices.Employee(emp_id=emp_id, db=db).get_employee()


    