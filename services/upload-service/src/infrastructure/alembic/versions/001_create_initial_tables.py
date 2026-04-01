"""Create initial tables diagramas and analises

Revision ID: 001
Revises:
Create Date: 2026-03-30

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
        "diagramas",
        sa.Column("id", sa.Uuid(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("nome_original", sa.String(255), nullable=False),
        sa.Column("content_type", sa.String(50), nullable=False),
        sa.Column("tamanho_bytes", sa.Integer(), nullable=False),
        sa.Column("storage_path", sa.String(512), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "analises",
        sa.Column("id", sa.Uuid(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("diagrama_id", sa.Uuid(), sa.ForeignKey("diagramas.id"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="recebido"),
        sa.Column("erro_detalhe", sa.Text(), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "status IN ('recebido', 'em_processamento', 'analisado', 'erro')",
            name="ck_analises_status",
        ),
    )

    op.create_index("idx_analises_status", "analises", ["status"])


def downgrade() -> None:
    op.drop_index("idx_analises_status", table_name="analises")
    op.drop_table("analises")
    op.drop_table("diagramas")
