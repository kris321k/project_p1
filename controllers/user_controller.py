from flask import Blueprint, request, jsonify
from dao.user_dao import UserDao
from services.user_service import UserService
from controllers.base_controller import (
    create_access_token,
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
@require_roles("MANAGER", "SYSTEM_ADMIN")
def create_user():
    try:
        data = get_payload()
        required = ("username", "email", "password", "role")
        missing = [field for field in required if data.get(field) in (None, "")]
        if missing:

            raise ValueError(f"Missing required fields: {', '.join(missing)}")
        user = user_service.save(data)
        if not user :
            return jsonify({
                "error" : "user not created"
            }), 400
        
        return jsonify({
            "message" : "created",
            "user" : serialize(user)
        }), 201
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
