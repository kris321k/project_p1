from datetime import datetime

from config.database import db


class ApprovalHistory(db.Model):

    __tablename__ = "approval_history"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    claim_id = db.Column(
        db.Integer,
        db.ForeignKey("expense_claims.id"),
        nullable=False
    )

    approver_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    action = db.Column(
        db.String(30),
        nullable=False
    )

    comment = db.Column(
        db.Text,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    claim = db.relationship(
        "ExpenseClaim",
        back_populates="approval_history"
    )

    approver = db.relationship(
        "User"
    )