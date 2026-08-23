import os
import uuid
from flask import Blueprint, current_app, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from dao.expense_receipt_dao import ExpenseReceiptDao
from services.receipt_service import ReceiptService
from services.expense_item_service import ExpenseItemService
from dao.expense_item_dao import ExpenseItemDao
from controllers.base_controller import current_employee_id, current_user_id, current_user_role, get_payload, require_auth, require_json_fields, require_roles, serialize
receipt_controller = Blueprint("receipt", __name__)
receipt_service = ReceiptService(ExpenseReceiptDao())
expense_item_service = ExpenseItemService(ExpenseItemDao())
ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg"}
ALLOWED_MIME_TYPES = {"application/pdf", "image/png", "image/jpeg"}
MAX_RECEIPT_SIZE = 10 * 1024 * 1024

def _receipt_extension(filename):
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

@receipt_controller.route("/receipts", methods=["GET"])
@require_auth
def get_receipts():
    item_id = request.args.get("expense_item_id", type=int)
    uploader_id = request.args.get("uploaded_by", type=int)
    if current_user_role() == "EMPLOYEE":
        uploader_id = current_user_id()
    if item_id:
        item = expense_item_service.get_by_id(item_id)
        if current_user_role() == "EMPLOYEE" and item.claim.employee_id != current_employee_id():
            return jsonify({"error": "Insufficient permissions"}), 403
        receipts = receipt_service.get_by_item(item_id)
    elif uploader_id:
        receipts = receipt_service.get_by_uploader(uploader_id)
    else:
        return jsonify({"error": "expense_item_id or uploaded_by is required"}), 400
    return jsonify([serialize(receipt) for receipt in receipts]), 200

@receipt_controller.route("/receipts/<int:receipt_id>", methods=["GET"])
@require_auth
def get_receipt(receipt_id):
    try:
        receipt = receipt_service.get_by_id(receipt_id)
        if current_user_role() == "EMPLOYEE" and receipt.expense_item.claim.employee_id != current_employee_id():
            return jsonify({"error": "Insufficient permissions"}), 403
        return jsonify(serialize(receipt))
    except Exception as error:
        return jsonify({"error": str(error)}), 404
    
@receipt_controller.route("/receipts", methods=["POST"])
@require_roles("EMPLOYEE", "MANAGER", "FINANCE_ADMIN", "ADMIN", "SYSTEM_ADMIN")
def create_receipt():
    try:
        data = get_payload()
        data["uploaded_by"] = current_user_id()
        require_json_fields(data, ("expense_item_id", "file_name", "file_path", "file_type", "file_size"))
        receipt = receipt_service.save(data)
        return jsonify({"message": "success", "receipt": serialize(receipt)}), 201
    except Exception as error:
        return jsonify({"error": str(error)}), 400

@receipt_controller.route("/receipts/upload", methods=["POST"])
@require_roles("EMPLOYEE", "MANAGER", "FINANCE_ADMIN", "ADMIN", "SYSTEM_ADMIN")
def upload_receipt():

    upload = request.files.get("file")
    expense_item_id = request.form.get("expense_item_id", type=int)

    if not upload or not upload.filename:
        return jsonify({"error": "A receipt file is required"}), 400

    if not expense_item_id:
        return jsonify({"error": "expense_item_id is required"}), 400

    extension = _receipt_extension(upload.filename)
    if extension not in ALLOWED_EXTENSIONS or upload.mimetype not in ALLOWED_MIME_TYPES:
        return jsonify({"error": "Only PDF, PNG, JPG, and JPEG receipts are supported"}), 400

    upload.seek(0, os.SEEK_END)
    file_size = upload.tell()
    upload.seek(0)

    if file_size > MAX_RECEIPT_SIZE:
        return jsonify({"error": "Receipt file must be 10 MB or smaller"}), 413

    item = expense_item_service.get_by_id(expense_item_id)
    if item is None:
        return jsonify({"error": "Expense item not found"}), 404

    if current_user_role() == "EMPLOYEE" and item.claim.employee_id != current_employee_id():
        return jsonify({"error": "You can only attach receipts to your own claim"}), 403
    if current_user_role() == "EMPLOYEE" and item.claim.status in {"VERIFIED", "REIMBURSED"}:
        return jsonify({"error": "Verified claims cannot be modified"}), 400

    safe_name = f"{uuid.uuid4().hex}.{extension}"
    dest_path = os.path.join(current_app.config["RECEIPT_UPLOAD_FOLDER"], safe_name)

    try:
        upload.save(dest_path)

        # 6. Save the receipt record in the database
        receipt = receipt_service.save({
            "expense_item_id": expense_item_id,
            "file_name": secure_filename(upload.filename),
            "file_path": safe_name,
            "file_type": upload.mimetype,
            "file_size": file_size,
            "uploaded_by": current_user_id(),
        })

        if receipt is None:
            # Clean up the file if the DB save failed
            if os.path.exists(dest_path):
                os.remove(dest_path)
            return jsonify({"error": "Receipt could not be saved"}), 500

        return jsonify({
            "message": "success",
            "receipt": serialize(receipt)
        }), 201

    except Exception:
        # Always clean up the file on any unexpected error
        if os.path.exists(dest_path):
            os.remove(dest_path)

        current_app.logger.exception("Failed to upload receipt")
        return jsonify({"error": "Upload failed"}), 500

@receipt_controller.route("/receipts/<int:receipt_id>/download", methods=["GET"])
@require_auth
def download_receipt(receipt_id):
    try:
        receipt = receipt_service.get_by_id(receipt_id)
        is_claim_manager = (
            current_user_role() == "MANAGER"
            and receipt.expense_item.claim.employee.manager_id == current_employee_id()
        )
        if current_user_role() not in {"FINANCE_ADMIN", "ADMIN", "SYSTEM_ADMIN"} and not is_claim_manager and receipt.uploaded_by != current_user_id():
            return jsonify({"error": "Insufficient permissions"}), 403
        return send_from_directory(
            current_app.config["RECEIPT_UPLOAD_FOLDER"],
            receipt.file_path,
            as_attachment=True,
            download_name=receipt.file_name,
        )
    except Exception as error:
        return jsonify({"error": str(error)}), 404

        
@receipt_controller.route("/receipts/<int:receipt_id>", methods=["DELETE"])
@require_roles("FINANCE_ADMIN", "ADMIN", "SYSTEM_ADMIN")
def delete_receipt(receipt_id):
    try:
        receipt = receipt_service.get_by_id(receipt_id)
        return jsonify({"message": "success", "deleted": receipt_service.delete(receipt)})
    except Exception as error:
        return jsonify({"error": str(error)}), 400

