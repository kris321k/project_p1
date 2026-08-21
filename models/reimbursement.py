from datetime import datetime

from config.database import db


class Reimbursement(db.Model):

    __tablename__ = "reimbursements"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    claim_id = db.Column(
        db.Integer,
        db.ForeignKey("expense_claims.id"),
        unique=True,
        nullable=False
    )

    amount = db.Column(
        db.Numeric(10, 2),
        nullable=False
    )

    payment_method = db.Column(
        db.String(50),
        nullable=True
    )

    transaction_reference = db.Column(
        db.String(150),
        nullable=True
    )

    status = db.Column(
        db.String(30),
        default="PENDING",
        nullable=False
    )

    processed_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )

    processed_at = db.Column(
        db.DateTime,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    claim = db.relationship(
        "ExpenseClaim",
        back_populates="reimbursement"
    )

    processor = db.relationship(
        "User"
    )