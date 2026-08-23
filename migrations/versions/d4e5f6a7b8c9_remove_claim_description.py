"""remove claim-level description

Revision ID: d4e5f6a7b8c9
Revises: c3f4e5a6b7c8
"""
from alembic import op
import sqlalchemy as sa

revision = "d4e5f6a7b8c9"
down_revision = "c3f4e5a6b7c8"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column("expense_claims", "description")


def downgrade():
    op.add_column("expense_claims", sa.Column("description", sa.Text(), nullable=True))
