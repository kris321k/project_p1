import os
from datetime import timedelta

from flask import Flask, render_template

from config.database import init_db, db

from models.user import User
from models.employee import Employee
from models.travel_request import TravelRequest
from models.expense_category import ExpenseCategory
from models.expense_policy import ExpensePolicy
from models.expense_claim import ExpenseClaim
from models.expense_item import ExpenseItem
from models.expense_receipt import ExpenseReceipt
from models.approval_history import ApprovalHistory
from models.reimbursement import Reimbursement
from flask_migrate import Migrate
from controllers.routes import register_api_controllers

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024
app.config["RECEIPT_UPLOAD_FOLDER"] = os.path.join(app.root_path, "uploads", "receipts")
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "development-jwt-secret-change-me")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(
    minutes=int(os.environ.get("JWT_ACCESS_TOKEN_MINUTES", "30"))
)

init_db(app)
os.makedirs(app.config["RECEIPT_UPLOAD_FOLDER"], exist_ok=True)
migrate = Migrate(app, db)
register_api_controllers(app)

@app.route("/")
def home():
    return render_template("login.html")


@app.route("/manager")
def manager_dashboard():
    return render_template("manager/dashboard.html", role="MANAGER")


@app.route("/employee")
def employee_dashboard():
    return render_template("employee/dashboard.html", role="EMPLOYEE")


@app.route("/employee/profile")
def employee_profile():
    return render_template("employee/view.html", role="EMPLOYEE", view="profile")


@app.route("/employee/travel")
def employee_travel():
    return render_template("employee/view.html", role="EMPLOYEE", view="travel")


@app.route("/employee/claims")
def employee_claims():
    return render_template("employee/view.html", role="EMPLOYEE", view="claims")


@app.route("/finance")
def finance_dashboard():
    return render_template("finance/dashboard.html", role="FINANCE_ADMIN")


@app.route("/admin")
def admin_dashboard():
    return render_template("admin/dashboard.html", role="ADMIN")


@app.route("/system-admin")
def system_admin_dashboard():
    return render_template("admin/system_dashboard.html", role="SYSTEM_ADMIN")


@app.route("/login")
def login():
    return render_template("login.html")


if __name__ == "__main__":
    app.run(debug=True)