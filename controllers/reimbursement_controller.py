from flask import Blueprint, request, jsonify
from dao.reimbursement_dao import ReimbursementDao
from services.reimbursement_service import ReimbursementService
from controllers.base_controller import current_user_id, get_payload, require_json_fields, require_roles, serialize
from controllers.claim_controller import claim_service
reimbursement_controller = Blueprint("reimbursement", __name__)
reimbursement_service = ReimbursementService(ReimbursementDao())
@reimbursement_controller.route("/reimbursements", methods=["GET"])
@require_roles("FINANCE", "ADMIN", "SYSTEM_ADMIN")
def get_reimbursements():
    claim_id = request.args.get("claim_id", type=int)
    status = request.args.get("status")
    processed_by = request.args.get("processed_by", type=int)
    if claim_id:
        items = reimbursement_service.get_by_claim(claim_id)
    elif status:
        items = reimbursement_service.get_by_status(status)
    elif processed_by:
        items = reimbursement_service.get_processed_by(processed_by)
    else:
        return jsonify({"error": "claim_id, status, or processed_by is required"}), 400
    return jsonify(serialize(items))

@reimbursement_controller.route("/reimbursements/<int:reimbursement_id>", methods=["GET"])
@require_roles("FINANCE", "ADMIN", "SYSTEM_ADMIN")
def get_reimbursement(reimbursement_id):
    try:
        return jsonify(serialize(reimbursement_service.get_by_id(reimbursement_id)))
    except Exception as error:
        return jsonify({"error": str(error)}), 404

@reimbursement_controller.route("/reimbursements", methods=["POST"])
@require_roles("FINANCE", "ADMIN", "SYSTEM_ADMIN")
def create_reimbursement():
    try:
        data = get_payload()
        require_json_fields(data, ("claim_id", "amount"))
        claim = claim_service.get_by_id(data["claim_id"])
        if claim.status not in {"APPROVED", "VERIFIED"}:
            raise ValueError("Only approved or verified claims can be reimbursed")
        if float(data["amount"]) > float(claim.total_amount):
            raise ValueError("Reimbursement cannot exceed the claim total")
        item = reimbursement_service.save(data)
        return jsonify({"message": "success", "reimbursement": serialize(item)}), 201
    except Exception as error:
        return jsonify({"error": str(error)}), 400
    
@reimbursement_controller.route("/reimbursements/<int:reimbursement_id>/process", methods=["PATCH"])
@require_roles("FINANCE", "ADMIN", "SYSTEM_ADMIN")
def process_reimbursement(reimbursement_id):
    try:
        data = get_payload()
        data["processed_by"] = current_user_id()
        require_json_fields(data, ("payment_method", "transaction_reference"))
        item = reimbursement_service.mark_as_processed(
            reimbursement_id,
            data["processed_by"],
            data["payment_method"],
            data["transaction_reference"],
        )
        return jsonify({"message": "success", "reimbursement": serialize(item)})
    except Exception as error:
        return jsonify({"error": str(error)}), 400
    