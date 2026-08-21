from datetime import datetime

from config.database import db


class ExpensePolicy(db.Model):

    __tablename__ = "expense_policies"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    category_id = db.Column(
        db.Integer,
        db.ForeignKey("expense_categories.id"),
        nullable=False
    )

    max_amount = db.Column(
        db.Numeric(10, 2),
        nullable=True
    )

    daily_limit = db.Column(
        db.Numeric(10, 2),
        nullable=True
    )

    requires_receipt = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )

    is_active = db.Column(
        db.Boolean,
        default=True,
        nullable=False
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

    category = db.relationship(
        "ExpenseCategory",
        back_populates="policies"
    )