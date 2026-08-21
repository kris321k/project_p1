from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError

from config.database import db
from models.employee import Employee


class EmployeeDao:
    """Persistence operations for employee profiles and reporting lines."""

    def create_employee(self, employee: Employee) -> Employee | None:
        try:
            db.session.add(employee)
            db.session.commit()
            return employee
        except SQLAlchemyError:
            db.session.rollback()
            return None
        
    def get_employee_by_id(self, employee_id: int) -> Employee | None:
        return db.session.get(Employee, employee_id)

    def get_employee_by_user_id(self, user_id: int) -> Employee | None:
        return db.session.scalar(db.select(Employee).where(Employee.user_id == user_id))

    def get_employee_by_code(self, employee_code: str) -> Employee | None:
        return db.session.scalar(
            db.select(Employee).where(Employee.employee_code == employee_code)
        )

    def get_employees_by_manager(self, manager_id: int) -> list[Employee]:
        return list(
            db.session.scalars(
                db.select(Employee)
                .where(Employee.manager_id == manager_id)
                .order_by(Employee.last_name, Employee.first_name)
            )
        )

    def search_employees(self, search_term: str) -> list[Employee]:
        pattern = f"%{search_term.strip()}%"
        return list(
            db.session.scalars(
                db.select(Employee)
                .where(
                    or_(
                        Employee.first_name.ilike(pattern),
                        Employee.last_name.ilike(pattern),
                        Employee.employee_code.ilike(pattern),
                        Employee.department.ilike(pattern),
                    )
                )
                .order_by(Employee.last_name, Employee.first_name)
            )
        )
    
    def get_all_employees(self) -> list[Employee]:
        return list(db.session.scalars(db.select(Employee).order_by(Employee.last_name)))

    def update_employee(self, employee: Employee) -> Employee | None:
        try:
            db.session.commit()
            return employee
        except SQLAlchemyError:
            db.session.rollback()
            return None

    def delete_employee(self, employee: Employee) -> bool:
        try:
            db.session.delete(employee)
            db.session.commit()
            return True
        except SQLAlchemyError:
            db.session.rollback()
            return False
