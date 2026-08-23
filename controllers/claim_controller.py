from flask import Blueprint, request, jsonify
from dao.expense_claim_dao import ExpenseClaimDao
from services.claim_service import ClaimService
from controllers.base_controller import current_employee_id, current_user_role, get_payload, require_auth, require_json_fields, require_roles, serialize, update_allowed
claim_controller = Blueprint("claim", __name__)
claim_service = ClaimService(ExpenseClaimDao())
@claim_controller.route("/claims", methods=["GET"])
@require_auth
def get_claims():
    employee_id = request.args.get("employee_id", type=int)
    status = request.args.get("status")
    search = request.args.get("search")
    if current_user_role() == "EMPLOYEE":
        employee_id = current_employee_id()
    if current_user_role() == "MANAGER":
        claims = claim_service.get_for_manager(current_employee_id(), status)
        if search:
            term = search.strip().lower()
            claims = [claim for claim in claims if term in claim.claim_number.lower()]
    elif search:
        claims = claim_service.search(search, employee_id)
    elif employee_id:
        claims = claim_service.get_by_employee(employee_id, status)
    elif status:
        claims = claim_service.get_by_status(status)
    else:
        claims = claim_service.get_all()
    return jsonify([serialize(claim) for claim in claims])

@claim_controller.route("/claims/<int:claim_id>", methods=["GET"])
@require_auth
def get_claim(claim_id):
    try:
        
        claim = claim_service.get_by_id(claim_id)
        if current_user_role() == "EMPLOYEE" and claim.employee_id != current_employee_id():
            return jsonify({"error": "Insufficient permissions"}), 403
        if current_user_role() == "MANAGER" and claim.employee.manager_id != current_employee_id():
            return jsonify({"error": "Insufficient permissions"}), 403
        return jsonify(serialize(claim))
    except Exception as error:
        return jsonify({"error": str(error)}), 404
    
@claim_controller.route("/claims", methods=["POST"])
@require_roles("EMPLOYEE", "MANAGER", "ADMIN", "SYSTEM_ADMIN")
def create_claim():
    try:
        data = get_payload()
        data["employee_id"] = current_employee_id()
        claim = claim_service.save(data)
        return jsonify({"message": "success", "claim": serialize(claim)}), 201
    except Exception as error:
        return jsonify({"error": str(error)}), 400
    
@claim_controller.route("/claims/<int:claim_id>/status", methods=["PATCH"])
@require_roles("MANAGER", "ADMIN", "SYSTEM_ADMIN")
def update_claim_status(claim_id):
    try:
        data = get_payload()
        require_json_fields(data, ("status",))
        next_status = data["status"].upper()
        if current_user_role() == "MANAGER" and next_status not in {"APPROVED", "REJECTED"}:
            raise ValueError("Managers can only approve or reject claims")
        claim = claim_service.get_by_id(claim_id)
        if current_user_role() == "MANAGER" and claim.employee.manager_id != current_employee_id():
            return jsonify({"error": "Insufficient permissions"}), 403
        claim = claim_service.update_status(claim_id, next_status)
        return jsonify({"message": "success", "claim": serialize(claim)})
    except Exception as error:
        return jsonify({"error": str(error)}), 400


@claim_controller.route("/claims/<int:claim_id>/submit", methods=["POST"])
@require_roles("EMPLOYEE", "MANAGER", "ADMIN", "SYSTEM_ADMIN")
def submit_claim(claim_id):
    try:
        claim = claim_service.get_by_id(claim_id)
        if claim.employee_id != current_employee_id():
            raise ValueError("You can only submit your own claim")
        return jsonify({"message": "success", "claim": serialize(claim_service.submit(claim))})
    except Exception as error:
        return jsonify({"error": str(error)}), 400


@claim_controller.route("/claims/<int:claim_id>", methods=["PUT"])
@require_roles("EMPLOYEE", "MANAGER", "ADMIN", "SYSTEM_ADMIN")
def update_claim(claim_id):
    try:
        claim = claim_service.get_by_id(claim_id)
        if current_user_role() == "EMPLOYEE" and claim.employee_id != current_employee_id():
            raise ValueError("You can only update your own claim")
        if current_user_role() == "EMPLOYEE" and claim.status in {"VERIFIED", "REIMBURSED"}:
            raise ValueError("Verified claims cannot be modified")
        update_allowed(claim, get_payload(), {"travel_request_id", "total_amount"})
        return jsonify({"message": "success", "claim": serialize(claim_service.update(claim))})
    except Exception as error:
        return jsonify({"error": str(error)}), 400
    
@claim_controller.route("/claims/<int:claim_id>", methods=["DELETE"])
@require_auth
def delete_claim(claim_id):
    try:
        claim = claim_service.get_by_id(claim_id)
        if current_user_role() == "EMPLOYEE" and claim.employee_id != current_employee_id():
            return jsonify({"error": "Insufficient permissions"}), 403
        return jsonify({"message": "success", "deleted": claim_service.delete(claim)})
    except Exception as error:
        return jsonify({"error": str(error)}), 400
