from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError
from dao.user_dao import UserDao
from services.user_service import UserService
from controllers.base_controller import (
    create_access_token,
    current_employee_id,
    current_user_role,
    get_payload,
    require_roles,
    serialize,
    update_allowed,
)

user_controller = Blueprint("user", __name__)
user_service = UserService(UserDao())

@user_controller.route("/users", methods=["GET"])
@require_roles("ADMIN", "SYSTEM_ADMIN")
def get_users():
    users = user_service.get_all()
    return jsonify([serialize(user) for user in users])

@user_controller.route("/users/<int:user_id>", methods=["GET"])
@require_roles("ADMIN", "SYSTEM_ADMIN")
def get_user(user_id):
    try:
        return jsonify(serialize(user_service.get_by_id(user_id)))
    except Exception as error:
        return jsonify({"error": str(error)}), 404
    
@user_controller.route("/users/register", methods=["POST"])
@require_roles("MANAGER", "ADMIN", "SYSTEM_ADMIN")
def create_user():
    try:
        data = get_payload()
        required = ("first_name", "last_name", "department", "phone", "email", "password", "role")
        missing = [field for field in required if data.get(field) in (None, "")]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
        data["first_name"] = data["first_name"].strip()
        data["last_name"] = data["last_name"].strip()
        data["department"] = data["department"].strip()
        data["phone"] = data["phone"].strip()
        data["email"] = data["email"].strip().lower()
        if user_service.get_by_email(data["email"]):
            return jsonify({"error": "Email already exists"}), 409
        role = data["role"].upper()
        data["role"] = role
        manager_id = None
        if current_user_role() == "MANAGER":
            if role != "EMPLOYEE":
                raise ValueError("Managers can register employees only")
            manager_id = current_employee_id()
        user = user_service.save(data, manager_id=manager_id)
        return jsonify({
            "message" : "created",
            "user" : {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "is_active": user.is_active,
            }
        }), 201
    except IntegrityError as error:
        constraint = str(error.orig).lower()
        if "username" in constraint:
            message = "Username already exists"
        elif "email" in constraint:
            message = "Email already exists"
        else:
            message = "A user with these details already exists"
        return jsonify({"error": message}), 409
    except Exception as error:
        return jsonify({"error": str(error)}), 400


@user_controller.route("/users/<int:user_id>", methods=["PUT"])
@require_roles("ADMIN", "SYSTEM_ADMIN")
def update_user(user_id):
    try:
        user = user_service.get_by_id(user_id)
        update_allowed(user, get_payload(), {"username", "email", "role", "is_active"})
        return jsonify({"message": "success", "user": serialize(user_service.update(user))})
    except Exception as error:
        return jsonify({"error": str(error)}), 400
    

@user_controller.route("/users/<int:user_id>", methods=["DELETE"])
@require_roles("ADMIN", "SYSTEM_ADMIN")
def delete_user(user_id):
    try:
        user = user_service.get_by_id(user_id)
        return jsonify({"message": "success", "deleted": user_service.delete(user)})
    except Exception as error:
        return jsonify({"error": str(error)}), 400
    
@user_controller.route("/users/sigin", methods=["POST"])
def authenticate_user():
    data = get_payload()
    required = ("email", "password")
    missing = [field for field in required if data.get(field) in (None, "")]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400
    user = user_service.authenticate({
        "email": data["email"],
        "password": data["password"],
    })
    if user is None:
        return jsonify({"error": "Invalid credentials"}), 401
    token = create_access_token(user)
    return jsonify({
        "access_token": token,
    })

@user_controller.route("/users/logout", methods=["POST"])
def logout():
    return jsonify({"message": "success", "detail": "Discard the access token on the client"})
