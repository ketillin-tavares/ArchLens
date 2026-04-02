"""Create relatorios table

Revision ID: 001
Revises:
Create Date: 2026-04-01

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "relatorios",
        sa.Column("id", sa.Uuid(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("analise_id", sa.Uuid(), nullable=False, unique=True),
        sa.Column("titulo", sa.String(255), nullable=True),
        sa.Column("resumo", sa.Text(), nullable=True),
        sa.Column("conteudo", sa.dialects.postgresql.JSONB(), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("idx_relatorios_analise", "relatorios", ["analise_id"], unique=True)


def downgrade() -> None:
    op.drop_index("idx_relatorios_analise", table_name="relatorios")
    op.drop_table("relatorios")
