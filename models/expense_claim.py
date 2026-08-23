from datetime import datetime
from config.database import db
class ExpenseClaim(db.Model):

    __tablename__ = "expense_claims"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    employee_id = db.Column(
        db.Integer,
        db.ForeignKey("employees.id"),
        nullable=False
    )

    travel_request_id = db.Column(
        db.Integer,
        db.ForeignKey("travel_requests.id"),
        nullable=True
    )
    claim_number = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )
    total_amount = db.Column(
        db.Numeric(10, 2),
        default=0,
        nullable=False
    )
    status = db.Column(
        db.String(40),
        default="DRAFT",
        nullable=False
    )
    submitted_at = db.Column(
        db.DateTime,
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
        back_populates="expense_claims"
    )

    travel_request = db.relationship(
        "TravelRequest",
        back_populates="expense_claims"
    )

    expense_items = db.relationship(
        "ExpenseItem",
        back_populates="claim",
        cascade="all, delete-orphan"
    )

    approval_history = db.relationship(
        "ApprovalHistory",
        back_populates="claim",
        cascade="all, delete-orphan"
    )

    reimbursement = db.relationship(
        "Reimbursement",
        back_populates="claim",
        uselist=False,
        cascade="all, delete-orphan"
    )