from flask import Blueprint, request, jsonify
from dao.travel_request_dao import TravelRequestDao
from services.travel_request_service import TravelRequestService
from controllers.base_controller import current_employee_id, current_user_role, get_payload, require_auth, require_json_fields, require_roles, serialize, update_allowed
travel_request_controller = Blueprint("travel_request", __name__)
travel_request_service = TravelRequestService(TravelRequestDao())

@travel_request_controller.route("/travel-requests", methods=["GET"])
@require_auth
def get_travel_requests():

    role = current_user_role()
    if role == "EMPLOYEE" :
        emp_id = current_employee_id()
        if not emp_id :
            return jsonify({
                "error" : "not authorized"
            }), 401
        requests = travel_request_service.get_by_employee(employee_id= emp_id)
        return jsonify([serialize(item) for item in requests])
    elif role == "MANAGER":
        requests = travel_request_service.get_for_manager(current_employee_id(), request.args.get("status"))
    elif request.args.get("status"):
        requests = travel_request_service.get_by_status(request.args["status"].upper())
    else:
        requests = travel_request_service.get_all()
    return jsonify([serialize(item) for item in requests])
    
@travel_request_controller.route("/travel-requests/<int:request_id>", methods=["GET"])
@require_auth
def get_travel_request(request_id):
    try:
        item = travel_request_service.get_by_id(request_id)
        if current_user_role() == "EMPLOYEE" and item.employee_id != current_employee_id():
            return jsonify({"error": "Insufficient permissions"}), 403
        return jsonify(serialize(item))
    except Exception as error:
        return jsonify({"error": str(error)}), 404
    
@travel_request_controller.route("/travel-requests", methods=["POST"])
@require_roles("EMPLOYEE", "MANAGER", "ADMIN", "SYSTEM_ADMIN")
def create_travel_request():
    try:
        data = get_payload()
        data["employee_id"] = current_employee_id()
        require_json_fields(data, ("destination", "purpose", "start_date", "end_date", "estimated_cost"))
        item = travel_request_service.save(data)
        return jsonify({"message": "success", "travel_request": serialize(item)}), 201
    except Exception as error:
        return jsonify({"error": str(error)}), 400
    
@travel_request_controller.route("/travel-requests", methods=["PATCH"])
@travel_request_controller.route("/travel-requests/", methods=["PATCH"])
@require_roles("MANAGER", "ADMIN", "SYSTEM_ADMIN")
def update_travel_status():
    try:
        data = get_payload()
        require_json_fields(
            data,
            ("request_id", "status")
        )

        item = travel_request_service.get_by_id(data["request_id"])
        if current_user_role() == "MANAGER" and item.employee.manager_id != current_employee_id():
            return jsonify({"error": "Insufficient permissions"}), 403
        status = data["status"].upper()
        if status not in {"APPROVED", "REJECTED"}:
            raise ValueError("Managers can only approve or reject travel requests")
        item = travel_request_service.update_status(
            data["request_id"],
            status,
            data.get("manager_comment")
        )
        return jsonify({"message": "success", "travel_request": serialize(item)}), 200
    except Exception as error:
        return jsonify({"error": str(error)}), 400
    
@travel_request_controller.route("/travel-requests/<int:request_id>", methods=["PUT"])
@require_roles("ADMIN", "SYSTEM_ADMIN")
def update_travel_request(request_id):
    try:
        item = travel_request_service.get_by_id(request_id)
        update_allowed(item, get_payload(), {"destination", "purpose", "start_date", "end_date", "estimated_cost", "manager_comment"})
        return jsonify({"message": "success", "travel_request": serialize(travel_request_service.update(item))})
    except Exception as error:
        return jsonify({"error": str(error)}), 400
    