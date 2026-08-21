"""seed standard expense categories

Revision ID: c3f4e5a6b7c8
Revises: 8ec2b8233308
"""
from alembic import op
import sqlalchemy as sa

revision = "c3f4e5a6b7c8"
down_revision = "8ec2b8233308"
branch_labels = None
depends_on = None


def upgrade():
    categories = sa.table(
        "expense_categories",
        sa.column("name", sa.String),
        sa.column("description", sa.Text),
        sa.column("is_active", sa.Boolean),
    )
    op.bulk_insert(categories, [
        {"name": "Accommodation", "description": "Hotels and lodging", "is_active": True},
        {"name": "Transportation", "description": "Ground transportation and taxis", "is_active": True},
        {"name": "Meals", "description": "Business meals and refreshments", "is_active": True},
        {"name": "Flight", "description": "Business air travel", "is_active": True},
        {"name": "Other business expenses", "description": "Other eligible business expenses", "is_active": True},
    ])


def downgrade():
    op.execute(
        "DELETE FROM expense_categories WHERE name IN "
        "('Accommodation', 'Transportation', 'Meals', 'Flight', 'Other business expenses')"
    )
