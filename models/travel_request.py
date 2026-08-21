from datetime import datetime

from config.database import db


class TravelRequest(db.Model):

    __tablename__ = "travel_requests"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    employee_id = db.Column(
        db.Integer,
        db.ForeignKey("employees.id"),
        nullable=False
    )

    destination = db.Column(
        db.String(150),
        nullable=False
    )

    purpose = db.Column(
        db.Text,
        nullable=False
    )

    start_date = db.Column(
        db.Date,
        nullable=False
    )

    end_date = db.Column(
        db.Date,
        nullable=False
    )

    estimated_cost = db.Column(
        db.Numeric(10, 2),
        nullable=False
    )

    status = db.Column(
        db.String(30),
        default="PENDING",
        nullable=False
    )

    manager_comment = db.Column(
        db.Text,
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

    employee = db.relationship(
        "Employee",
        back_populates="travel_requests"
    )

    expense_claims = db.relationship(
        "ExpenseClaim",
        back_populates="travel_request"
    )