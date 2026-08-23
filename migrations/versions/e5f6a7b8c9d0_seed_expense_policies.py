"""seed standard expense policies

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
"""
from datetime import datetime

from alembic import op
import sqlalchemy as sa

revision = "e5f6a7b8c9d0"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None

POLICIES = {
    "Accommodation": (10000, 15000),
    "Transportation": (5000, 5000),
    "Meals": (2000, 3000),
    "Flight": (25000, 50000),
    "Other business expenses": (5000, 10000),
}


def upgrade():
    connection = op.get_bind()
    now = datetime.utcnow()
    for category_name, (max_amount, daily_limit) in POLICIES.items():
        category_id = connection.execute(
            sa.text("SELECT id FROM expense_categories WHERE name = :name"),
            {"name": category_name},
        ).scalar()
        if category_id is None:
            continue
        existing = connection.execute(
            sa.text("SELECT id FROM expense_policies WHERE category_id = :category_id AND is_active = 1 LIMIT 1"),
            {"category_id": category_id},
        ).scalar()
        if existing is None:
            connection.execute(
                sa.text("""
                    INSERT INTO expense_policies
                    (category_id, max_amount, daily_limit, requires_receipt, is_active, created_at, updated_at)
                    VALUES (:category_id, :max_amount, :daily_limit, :requires_receipt, :is_active, :created_at, :updated_at)
                """),
                {
                    "category_id": category_id,
                    "max_amount": max_amount,
                    "daily_limit": daily_limit,
                    "requires_receipt": True,
                    "is_active": True,
                    "created_at": now,
                    "updated_at": now,
                },
            )


def downgrade():
    connection = op.get_bind()
    for category_name in POLICIES:
        connection.execute(
            sa.text("""
                DELETE expense_policies FROM expense_policies
                JOIN expense_categories ON expense_categories.id = expense_policies.category_id
                WHERE expense_categories.name = :name
            """),
            {"name": category_name},
        )
