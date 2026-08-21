from flask import Blueprint, request, jsonify

from dao.expense_policy_dao import ExpensePolicyDao
from services.policy_service import PolicyService
from controllers.base_controller import get_payload, require_json_fields, require_roles, serialize, update_allowed

policy_controller = Blueprint("policy", __name__)
policy_service = PolicyService(ExpensePolicyDao())


@policy_controller.route("/policies", methods=["GET"])
@require_roles("EMPLOYEE", "MANAGER", "FINANCE", "ADMIN", "SYSTEM_ADMIN")
def get_policies():
    category_id = request.args.get("category_id", type=int)
    policies = policy_service.get_by_category(category_id) if category_id else policy_service.get_active()
    return jsonify([serialize(policy) for policy in policies])


@policy_controller.route("/policies/<int:policy_id>", methods=["GET"])
@require_roles("EMPLOYEE", "MANAGER", "FINANCE", "ADMIN", "SYSTEM_ADMIN")
def get_policy(policy_id):
    try:
        return jsonify(serialize(policy_service.get_by_id(policy_id)))
    except Exception as error:
        return jsonify({"error": str(error)}), 404


@policy_controller.route("/policies", methods=["POST"])
@require_roles("ADMIN", "SYSTEM_ADMIN")
def create_policy():
    try:
        data = get_payload()
        require_json_fields(data, ("category_id",))
        policy = policy_service.save(data)
        return jsonify({"message": "success", "policy": serialize(policy)}), 201
    except Exception as error:
        return jsonify({"error": str(error)}), 400


@policy_controller.route("/policies/<int:policy_id>", methods=["DELETE"])
@require_roles("ADMIN", "SYSTEM_ADMIN")
def deactivate_policy(policy_id):
    try:
        policy = policy_service.deactivate(policy_id)
        return jsonify({"message": "success", "policy": serialize(policy)})
    except Exception as error:
        return jsonify({"error": str(error)}), 400


@policy_controller.route("/policies/<int:policy_id>", methods=["PUT"])
@require_roles("ADMIN", "SYSTEM_ADMIN")
def update_policy(policy_id):
    try:
        policy = policy_service.get_by_id(policy_id)
        update_allowed(policy, get_payload(), {"category_id", "max_amount", "daily_limit", "requires_receipt", "is_active"})
        return jsonify({"message": "success", "policy": serialize(policy_service.update(policy))})
    except Exception as error:
        return jsonify({"error": str(error)}), 400
