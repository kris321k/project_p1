from flask import Blueprint, request, jsonify
from dao.expense_item_dao import ExpenseItemDao
from services.expense_item_service import ExpenseItemService
from controllers.claim_controller import claim_service
from controllers.base_controller import current_employee_id, current_user_role, get_payload, require_auth, require_json_fields, require_roles, serialize, update_allowed

expense_item_controller = Blueprint("expense_item", __name__)
expense_item_service = ExpenseItemService(ExpenseItemDao())

@expense_item_controller.route("/expense-items", methods=["GET"])
@require_auth
def get_expense_items():
    claim_id = request.args.get("claim_id", type=int)
    category_id = request.args.get("category_id", type=int)
    if claim_id:
        claim = claim_service.get_by_id(claim_id)
        if current_user_role() == "EMPLOYEE" and claim.employee_id != current_employee_id():
            return jsonify({"error": "Insufficient permissions"}), 403
        items = expense_item_service.get_by_claim(claim_id)
    elif category_id:
        items = expense_item_service.get_by_category(category_id)
    else:
        return jsonify({"error": "claim_id or category_id is required"}), 400
    return jsonify([serialize(item) for item in items])

@expense_item_controller.route("/expense-items/<int:item_id>", methods=["GET"])
@require_auth
def get_expense_item(item_id):
    try:
        item = expense_item_service.get_by_id(item_id)
        if current_user_role() == "EMPLOYEE" and item.claim.employee_id != current_employee_id():
            return jsonify({"error": "Insufficient permissions"}), 403
        return jsonify(serialize(item))
    except Exception as error:
        return jsonify({"error": str(error)}), 404


@expense_item_controller.route("/expense-items", methods=["POST"])
@require_roles("EMPLOYEE", "MANAGER", "ADMIN", "SYSTEM_ADMIN")
def create_expense_item():
    try:
        print("hii")
        data = get_payload()
        require_json_fields(data, ("claim_id", "category_id", "description", "amount", "expense_date"))
        item_claim = claim_service.get_by_id(data["claim_id"])
        if current_user_role() == "EMPLOYEE" and item_claim.employee_id != current_employee_id():
            return jsonify({"error": "You can only add items to your own claim"}), 403
        if current_user_role() == "EMPLOYEE" and item_claim.status in {"VERIFIED", "REIMBURSED"}:
            return jsonify({"error": "Verified claims cannot be modified"}), 400
        item = expense_item_service.save(data)
        return jsonify({"message": "success", "expense_item": serialize(item)}), 201
    except Exception as error:
        return jsonify({"error": str(error)}), 400


@expense_item_controller.route("/expense-items/<int:item_id>", methods=["PUT"])
@require_roles("EMPLOYEE", "MANAGER", "ADMIN", "SYSTEM_ADMIN")
def update_expense_item(item_id):
    try:
        item = expense_item_service.get_by_id(item_id)
        if current_user_role() == "EMPLOYEE" and item.claim.employee_id != current_employee_id():
            raise ValueError("You can only update your own expense item")
        if current_user_role() == "EMPLOYEE" and item.claim.status in {"VERIFIED", "REIMBURSED"}:
            raise ValueError("Verified claims cannot be modified")
        update_allowed(item, get_payload(), {"category_id", "description", "amount", "expense_date", "merchant"})
        return jsonify({"message": "success", "expense_item": serialize(expense_item_service.update(item))})
    except Exception as error:
        return jsonify({"error": str(error)}), 400


@expense_item_controller.route("/expense-items/<int:item_id>", methods=["DELETE"])
@require_roles("EMPLOYEE", "MANAGER", "ADMIN", "SYSTEM_ADMIN")
def delete_expense_item(item_id):
    try:
        item = expense_item_service.get_by_id(item_id)
        if current_user_role() == "EMPLOYEE" and item.claim.employee_id != current_employee_id():
            return jsonify({"error": "Insufficient permissions"}), 403
        if current_user_role() == "EMPLOYEE" and item.claim.status in {"VERIFIED", "REIMBURSED"}:
            return jsonify({"error": "Verified claims cannot be modified"}), 400
        return jsonify({"message": "success", "deleted": expense_item_service.delete(item)})
    except Exception as error:
        return jsonify({"error": str(error)}), 400
