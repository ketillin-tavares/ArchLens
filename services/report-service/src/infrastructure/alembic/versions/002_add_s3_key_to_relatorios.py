"""Add s3_key column to relatorios

Revision ID: 002
Revises: 001
Create Date: 2026-04-05

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "relatorios",
        sa.Column("s3_key", sa.String(512), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("relatorios", "s3_key")
