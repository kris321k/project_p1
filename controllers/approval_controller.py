from flask import Blueprint, request, jsonify

from dao.approval_history_dao import ApprovalHistoryDao
from services.approval_service import ApprovalService
from controllers.base_controller import current_employee_id, current_user_id, current_user_role, get_payload, require_json_fields, require_roles, serialize
from controllers.claim_controller import claim_service
approval_controller = Blueprint("approval", __name__)
approval_service = ApprovalService(ApprovalHistoryDao())

@approval_controller.route("/approvals", methods=["GET"])
@require_roles("MANAGER", "FINANCE", "ADMIN", "SYSTEM_ADMIN")
def get_approvals():
    claim_id = request.args.get("claim_id", type=int)
    approver_id = request.args.get("approver_id", type=int)
    if claim_id:
        records = approval_service.get_by_claim(claim_id)
    elif approver_id:
        records = approval_service.get_by_approver(approver_id)
    else:
        return jsonify({"error": "claim_id or approver_id is required"}), 400
    return jsonify([serialize(record) for record in records])

@approval_controller.route("/approvals", methods=["POST"])
@require_roles("MANAGER", "FINANCE", "ADMIN", "SYSTEM_ADMIN")
def create_approval():
    try:
        data = get_payload()
        data["approver_id"] = current_user_id()
        require_json_fields(data, ("claim_id", "action"))
        action = data["action"].upper()
        if action not in {"APPROVE", "REJECT", "VERIFY"}:
            raise ValueError("Action must be APPROVE, REJECT, or VERIFY")
        if current_user_role() == "MANAGER" and action not in {"APPROVE", "REJECT"}:
            raise ValueError("Managers can only approve or reject claims")
        if current_user_role() == "FINANCE" and action not in {"VERIFY", "REJECT"}:
            raise ValueError("Finance can only verify or reject claims")
        claim = claim_service.get_by_id(data["claim_id"])
        if current_user_role() == "MANAGER" and claim.employee.manager_id != current_employee_id():
            return jsonify({"error": "Insufficient permissions"}), 403
        record = approval_service.save(data)
        claim_service.update_status(claim.id, {"APPROVE": "APPROVED", "REJECT": "REJECTED", "VERIFY": "VERIFIED"}[action])
        return jsonify({"message": "success", "approval": serialize(record)}), 201
    except Exception as error:
        return jsonify({"error": str(error)}), 400
