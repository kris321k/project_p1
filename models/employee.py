from datetime import datetime

from config.database import db


class Employee(db.Model):

    __tablename__ = "employees"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        unique=True,
        nullable=False
    )

    employee_code = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    first_name = db.Column(
        db.String(100),
        nullable=False
    )

    last_name = db.Column(
        db.String(100),
        nullable=False
    )

    department = db.Column(
        db.String(100),
        nullable=False
    )

    designation = db.Column(
        db.String(100),
        nullable=False
    )

    phone = db.Column(
        db.String(20),
        nullable=True
    )

    manager_id = db.Column(
        db.Integer,
        db.ForeignKey("employees.id"),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # User account
    user = db.relationship(
        "User",
        back_populates="employee"
    )

    # Employee -> Manager
    manager = db.relationship(
        "Employee",
        remote_side=[id],
        back_populates="subordinates"
    )

    subordinates = db.relationship(
        "Employee",
        back_populates="manager"
    )

    # Employee -> Travel Requests
    travel_requests = db.relationship(
        "TravelRequest",
        back_populates="employee",
        cascade="all, delete-orphan"
    )

    # Employee -> Expense Claims
    expense_claims = db.relationship(
        "ExpenseClaim",
        back_populates="employee"
    )