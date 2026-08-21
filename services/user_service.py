from werkzeug.security import check_password_hash, generate_password_hash
from dao.employee_dao import EmployeeDao
from dao.user_dao import UserDao
from models.employee import Employee
from models.user import User
class UserService:

    def __init__(self, user_dao: UserDao):
        self.user_dao = user_dao

    def get_all(self) -> list[User]:
        return self.user_dao.get_all_users()
    
    def get_by_id(self, user_id: int) -> User:
        user = self.user_dao.get_user_by_id(user_id)
        if user is None:
            raise ValueError("User not found")
        return user
    
    def get_by_email(self, email: str) -> User | None:
        return self.user_dao.get_user_by_email(email)
    
    def get_by_username(self, username: str) -> User | None:
        return self.user_dao.get_user_by_username(username)
    
    def save(self, data: dict) -> User:
        user = User(
            username=data["username"],
            email=data["email"],
            password_hash=generate_password_hash(data["password"]),
            role=data["role"],
        )
        return self.user_dao.create_user(user)
    
    def authenticate(self, data : dict) -> User | None:
        user = self.get_by_email(data["email"]) 
        if user is None or not user.is_active:
            return None
        if not check_password_hash(user.password_hash, data["password"]):
            return None
        self.ensure_employee_profile(user)
        return user
    
    def ensure_employee_profile(self, user: User) -> Employee | None:
        if user.role.upper() not in {"EMPLOYEE", "MANAGER", "ADMIN", "SYSTEM_ADMIN"}:
            return None
        employee = EmployeeDao().get_employee_by_user_id(user.id)
        if employee is not None:
            return employee
        first_name = user.username.split("@", 1)[0][:100]
        employee = Employee(
            user_id=user.id,
            employee_code=f"EMP-{user.id:06d}",
            first_name=first_name or "Employee",
            last_name="User",
            department="Unassigned",
            designation=user.role.title(),
        )
        return EmployeeDao().create_employee(employee)

    
    def update(self, user: User) -> User | None:
        return self.user_dao.update_user(user)
    
    def delete(self, user: User) -> bool:
        return self.user_dao.delete_user(user)