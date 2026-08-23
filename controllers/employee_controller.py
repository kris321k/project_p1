from flask import Blueprint, request, jsonify
from dao.employee_dao import EmployeeDao
from services.employee_service import EmployeeService
from controllers.base_controller import current_employee_id, current_user_id, current_user_role, get_payload, require_auth, require_json_fields, require_roles, serialize, update_allowed

employee_controller = Blueprint("employee", __name__)
employee_service = EmployeeService(EmployeeDao())

@employee_controller.route("/employees/me", methods=["GET"])
@require_auth
def get_my_employee():
    employee = employee_service.get_by_user_id(current_user_id())
    if employee is None:
        return jsonify({"error": "Employee profile not found"}), 404
    return jsonify(serialize(employee))


@employee_controller.route("/employees/me", methods=["PUT"])
@require_auth
def update_my_employee():
    try:
        employee = employee_service.get_by_user_id(current_user_id())
        if employee is None:
            raise ValueError("Employee profile not found")
        update_allowed(employee, get_payload(), {"first_name", "last_name", "department", "designation", "phone"})
        return jsonify({"message": "success", "employee": serialize(employee_service.update(employee))})
    except Exception as error:
        return jsonify({"error": str(error)}), 400


@employee_controller.route("/employees", methods=["GET"])
@require_roles("ADMIN", "SYSTEM_ADMIN", "MANAGER", "FINANCE_ADMIN")
def get_employees():
    search = request.args.get("search")
    if current_user_role() == "MANAGER":
        employees = employee_service.get_by_manager(current_employee_id())
        if search:
            term = search.strip().lower()
            employees = [
                employee for employee in employees
                if term in f"{employee.first_name} {employee.last_name} {employee.employee_code} {employee.department}".lower()
            ]
    else:
        employees = employee_service.search(search) if search else employee_service.get_all()
    return jsonify([serialize(employee) for employee in employees])


@employee_controller.route("/employees/<int:employee_id>", methods=["GET"])
@require_auth
def get_employee(employee_id):
    try:
        if current_user_role() == "EMPLOYEE" and employee_id != current_employee_id():
            return jsonify({"error": "Insufficient permissions"}), 403
        return jsonify(serialize(employee_service.get_by_id(employee_id)))
    except Exception as error:
        return jsonify({"error": str(error)}), 404
    
@employee_controller.route("/employees", methods=["POST"])
@require_roles("ADMIN", "SYSTEM_ADMIN")
def create_employee():
    try:
        data = get_payload()
        require_json_fields(data, ("user_id", "employee_code", "first_name", "last_name", "department", "designation"))
        employee = employee_service.save(data)
        return jsonify({"message": "success", "employee": serialize(employee)}), 201
    except Exception as error:
        return jsonify({"error": str(error)}), 400

@employee_controller.route("/employees/<int:employee_id>", methods=["PUT"])
@require_roles("ADMIN", "SYSTEM_ADMIN")
def update_employee(employee_id):
    try:
        employee = employee_service.get_by_id(employee_id)
        update_allowed(employee, get_payload(), {"first_name", "last_name", "department", "designation", "phone", "manager_id"})
        return jsonify({"message": "success", "employee": serialize(employee_service.update(employee))})
    except Exception as error:
        return jsonify({"error": str(error)}), 400

    