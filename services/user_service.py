from werkzeug.security import check_password_hash, generate_password_hash
from dao.employee_dao import EmployeeDao
from dao.user_dao import UserDao
from models.employee import Employee
from models.user import User
import re
import uuid
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
    
    def save(self, data: dict, manager_id: int | None = None) -> User:
        email = data["email"].strip().lower()
        if self.get_by_email(email):
            raise ValueError("Email already exists")
        username = data.get("username") or re.sub(r"[^a-z0-9._-]", "", email.split("@", 1)[0].lower())
        username = username[:90] or "employee"
        while self.get_by_username(username):
            username = f"{username[:81]}-{uuid.uuid4().hex[:8]}"
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(data["password"]),
            role=data["role"],
        )
        user = self.user_dao.create_user(user)
        if user.role.upper() in {"EMPLOYEE", "MANAGER", "ADMIN", "SYSTEM_ADMIN"}:
            self.ensure_employee_profile(
                user,
                manager_id=manager_id,
                profile_data=data,
            )
        return user
    
    def authenticate(self, data : dict) -> User | None:
        user = self.get_by_email(data["email"]) 
        if user is None or not user.is_active:
            return None
        if not check_password_hash(user.password_hash, data["password"]):
            return None
        self.ensure_employee_profile(user)
        return user
    
    def ensure_employee_profile(self, user: User, manager_id: int | None = None, profile_data: dict | None = None) -> Employee | None:
        if user.role.upper() not in {"EMPLOYEE", "MANAGER", "ADMIN", "SYSTEM_ADMIN"}:
            return None
        employee = EmployeeDao().get_employee_by_user_id(user.id)
        if employee is not None:
            return employee
        profile_data = profile_data or {}
        employee = Employee(
            user_id=user.id,
            employee_code=f"EMP-{user.id:06d}",
            first_name=profile_data.get("first_name") or user.username.split("@", 1)[0][:100] or "Employee",
            last_name=profile_data.get("last_name") or "User",
            department=profile_data.get("department") or "Unassigned",
            designation=profile_data.get("designation") or user.role.title(),
            phone=profile_data.get("phone"),
            manager_id=manager_id,
        )
        return EmployeeDao().create_employee(employee)
    
    def update(self, user: User) -> User | None:
        return self.user_dao.update_user(user)
    
    def delete(self, user: User) -> bool:
        return self.user_dao.delete_user(user)