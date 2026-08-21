from flask import Blueprint, request, jsonify
from dao.expense_category_dao import ExpenseCategoryDao
from services.category_service import CategoryService
from controllers.base_controller import get_payload, require_json_fields, require_roles, serialize, update_allowed
category_controller = Blueprint("category", __name__)
category_service = CategoryService(ExpenseCategoryDao())


@category_controller.route("/categories", methods=["GET"])
@require_roles("EMPLOYEE", "MANAGER", "FINANCE", "ADMIN", "SYSTEM_ADMIN")
def get_categories():
    categories = category_service.get_active() if request.args.get("active") else category_service.get_all()
    return jsonify([serialize(category) for category in categories])

@category_controller.route("/categories/<int:category_id>", methods=["GET"])
@require_roles("EMPLOYEE", "MANAGER", "FINANCE", "ADMIN", "SYSTEM_ADMIN")
def get_category(category_id):
    try:
        return jsonify(serialize(category_service.get_by_id(category_id)))
    except Exception as error:
        return jsonify({"error": str(error)}), 404
    
@category_controller.route("/categories", methods=["POST"])
@require_roles("ADMIN", "SYSTEM_ADMIN")
def create_category():
    try:
        data = get_payload()
        require_json_fields(data, ("name",))
        category = category_service.save(data)
        return jsonify({"message": "success", "category": serialize(category)}), 201
    except Exception as error:
        return jsonify({"error": str(error)}), 400
    
@category_controller.route("/categories/<int:category_id>", methods=["DELETE"])
@require_roles("ADMIN", "SYSTEM_ADMIN")
def deactivate_category(category_id):
    try:
        category = category_service.deactivate(category_id)
        return jsonify({"message": "success", "category": serialize(category)})
    except Exception as error:
        return jsonify({"error": str(error)}), 400
    
@category_controller.route("/categories/<int:category_id>", methods=["PUT"])
@require_roles("ADMIN", "SYSTEM_ADMIN")
def update_category(category_id):
    try:
        category = category_service.get_by_id(category_id)
        update_allowed(category, get_payload(), {"name", "description", "is_active"})
        return jsonify({"message": "success", "category": serialize(category_service.update(category))})
    except Exception as error:
        return jsonify({"error": str(error)}), 400
