from datetime import date, datetime
from decimal import Decimal
from functools import wraps
import jwt
from flask import current_app, g, jsonify, request
from config.database import db
from models.employee import Employee

def serialize(value):
    if hasattr(value, "__table__"):
        return {
            column.name: serialize(getattr(value, column.name))
            for column in value.__table__.columns
        }
    
    if isinstance(value, list):
        return [serialize(item) for item in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    return value

def jsonify_data(value, status_code=200):
    return jsonify(serialize(value)), status_code

def jsonify_message(message, value=None, status_code=200):
    response = {"message": message}
    if value is not None:
        response["data"] = serialize(value)
    return jsonify(response), status_code

def jsonify_error(error, status_code=400):
    return jsonify({"error": str(error)}), status_code

def get_payload():
    return request.get_json(silent=True) or {}

def require_json_fields(data, fields):
    missing = [field for field in fields if data.get(field) in (None, "")]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")
    
def update_allowed(model, data, allowed_fields):

    unknown = set(data) - set(allowed_fields)
    if unknown:
        raise ValueError(f"Unsupported fields: {', '.join(sorted(unknown))}")
    for field, value in data.items():
        setattr(model, field, value)
    return model

def create_access_token(user):
    now = datetime.utcnow()
    expires_at = now + current_app.config["JWT_ACCESS_TOKEN_EXPIRES"]
    payload = {
        "sub": str(user.id),
        "role": user.role.upper(),
        "employee_id": user.employee.id if user.employee else None,
        "iat": now,
        "exp": expires_at,
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET_KEY"], algorithm="HS256")

def decode_access_token():

    authorization = request.headers.get("Authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise ValueError("Bearer token required")
    try:
        return jwt.decode(
            token,
            current_app.config["JWT_SECRET_KEY"],
            algorithms=["HS256"],
            options={"require": ["sub", "role", "iat", "exp"]},
        )
    
    except jwt.ExpiredSignatureError as error:
        raise ValueError("Token has expired") from error
    except jwt.InvalidTokenError as error:
        raise ValueError("Invalid token") from error
    
def current_user_id():
    return g.current_user_id

def current_user_role():
    return g.current_user_role

def current_employee_id():
    employee_id = getattr(g, "current_employee_id", None)
    if employee_id is None:
        raise ValueError("Authenticated user is not linked to an employee")
    return employee_id

def _set_authenticated_identity(claims):
    g.current_user_id = int(claims["sub"])
    employee_id = claims.get("employee_id")
    if employee_id is None:
        employee = db.session.scalar(
            db.select(Employee).where(Employee.user_id == g.current_user_id)
        )
        employee_id = employee.id if employee else None
    g.current_employee_id = int(employee_id) if employee_id is not None else None
    g.current_user_role = claims["role"].upper()

def require_auth(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        try:
            claims = decode_access_token()
            _set_authenticated_identity(claims)
        except (ValueError, TypeError):
            return jsonify({"error": "Authentication required"}), 401
        return view(*args, **kwargs)
    return wrapped

def require_roles(*roles):
    allowed_roles = {role.upper() for role in roles}
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            try:
                claims = decode_access_token()
                _set_authenticated_identity(claims)
            except (ValueError, TypeError):
                return jsonify({"error": "Authentication required"}), 401
            if g.current_user_role not in allowed_roles:
                return jsonify({"error": "Insufficient permissions"}), 403
            return view(*args, **kwargs)
        return wrapped
    return decorator

