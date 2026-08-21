from datetime import datetime

from config.database import db


class ExpenseItem(db.Model):

    __tablename__ = "expense_items"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    claim_id = db.Column(
        db.Integer,
        db.ForeignKey("expense_claims.id"),
        nullable=False
    )

    category_id = db.Column(
        db.Integer,
        db.ForeignKey("expense_categories.id"),
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=False
    )

    amount = db.Column(
        db.Numeric(10, 2),
        nullable=False
    )

    expense_date = db.Column(
        db.Date,
        nullable=False
    )

    merchant = db.Column(
        db.String(150),
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

    claim = db.relationship(
        "ExpenseClaim",
        back_populates="expense_items"
    )

    category = db.relationship(
        "ExpenseCategory",
        back_populates="expense_items"
    )

    receipts = db.relationship(
        "ExpenseReceipt",
        back_populates="expense_item",
        cascade="all, delete-orphan"
    )