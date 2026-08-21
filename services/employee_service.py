from dao.employee_dao import EmployeeDao
from models.employee import Employee


class EmployeeService:
    """Thin application service for Employee persistence."""

    def __init__(self, employee_dao: EmployeeDao):
        self.employee_dao = employee_dao

    def get_all(self) -> list[Employee]:
        return self.employee_dao.get_all_employees()

    def get_by_id(self, employee_id: int) -> Employee:
        employee = self.employee_dao.get_employee_by_id(employee_id)
        if employee is None:
            raise ValueError("Employee not found")
        return employee
    
    def get_by_user_id(self, user_id: int) -> Employee | None:
        return self.employee_dao.get_employee_by_user_id(user_id)

    def get_by_code(self, employee_code: str) -> Employee | None:
        return self.employee_dao.get_employee_by_code(employee_code)

    def get_by_manager(self, manager_id: int) -> list[Employee]:
        return self.employee_dao.get_employees_by_manager(manager_id)

    def search(self, search_term: str) -> list[Employee]:
        return self.employee_dao.search_employees(search_term)

    def save(self, data: dict) -> Employee:
        employee = Employee(
            user_id=data["user_id"],
            employee_code=data["employee_code"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            department=data["department"],
            designation=data["designation"],
            phone=data.get("phone"),
            manager_id=data.get("manager_id"),
        )
        return self.employee_dao.create_employee(employee)

    def update(self, employee: Employee) -> Employee | None:
        return self.employee_dao.update_employee(employee)

    def delete(self, employee: Employee) -> bool:
        return self.employee_dao.delete_employee(employee)
