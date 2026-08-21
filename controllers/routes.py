from controllers.approval_controller import approval_controller
from controllers.category_controller import category_controller
from controllers.claim_controller import claim_controller
from controllers.employee_controller import employee_controller
from controllers.expense_item_controller import expense_item_controller
from controllers.policy_controller import policy_controller
from controllers.receipt_controller import receipt_controller
from controllers.reimbursement_controller import reimbursement_controller
from controllers.travel_request_controller import travel_request_controller
from controllers.user_controller import user_controller


def register_api_controllers(app):
    """Register module-level API controller blueprints."""
    controllers = [
        user_controller,
        employee_controller,
        travel_request_controller,
        claim_controller,
        expense_item_controller,
        receipt_controller,
        approval_controller,
        reimbursement_controller,
        category_controller,
        policy_controller,
    ]
    for controller in controllers:
        app.register_blueprint(controller, url_prefix="/api")
    return controllers
