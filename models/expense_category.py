from datetime import datetime

from config.database import db


class ExpenseCategory(db.Model):

    __tablename__ = "expense_categories"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=True
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

    expense_items = db.relationship(
        "ExpenseItem",
        back_populates="category"
    )

    policies = db.relationship(
        "ExpensePolicy",
        back_populates="category",
        cascade="all, delete-orphan"
    )