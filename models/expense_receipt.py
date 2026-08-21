from datetime import datetime

from config.database import db


class ExpenseReceipt(db.Model):

    __tablename__ = "expense_receipts"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    expense_item_id = db.Column(
        db.Integer,
        db.ForeignKey("expense_items.id"),
        nullable=False
    )

    file_name = db.Column(
        db.String(255),
        nullable=False
    )

    file_path = db.Column(
        db.String(500),
        nullable=False
    )

    file_type = db.Column(
        db.String(50),
        nullable=False
    )

    file_size = db.Column(
        db.Integer,
        nullable=False
    )

    uploaded_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    uploaded_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    expense_item = db.relationship(
        "ExpenseItem",
        back_populates="receipts"
    )

    uploader = db.relationship(
        "User"
    )