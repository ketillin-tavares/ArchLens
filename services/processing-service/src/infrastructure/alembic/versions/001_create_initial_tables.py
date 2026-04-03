"""Create processamentos, componentes, riscos and risco_componentes tables

Revision ID: 001
Revises:
Create Date: 2026-04-02

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "processamentos",
        sa.Column("id", sa.Uuid(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("analise_id", sa.Uuid(), nullable=False, unique=True),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="pendente",
        ),
        sa.Column("tentativas", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("iniciado_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("concluido_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("erro_detalhe", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("status IN ('pendente','executando','concluido','erro')", name="ck_processamentos_status"),
    )
    op.create_index("idx_processamentos_analise", "processamentos", ["analise_id"], unique=True)

    op.create_table(
        "componentes",
        sa.Column("id", sa.Uuid(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("processamento_id", sa.Uuid(), nullable=False),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.Column("tipo", sa.String(50), nullable=False),
        sa.Column("confianca", sa.Float(), nullable=False, server_default=sa.text("0.0")),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["processamento_id"], ["processamentos.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "riscos",
        sa.Column("id", sa.Uuid(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("processamento_id", sa.Uuid(), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=False),
        sa.Column("severidade", sa.String(10), nullable=False),
        sa.Column("recomendacao_descricao", sa.Text(), nullable=True),
        sa.Column("recomendacao_prioridade", sa.String(10), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["processamento_id"], ["processamentos.id"], ondelete="CASCADE"),
        sa.CheckConstraint("severidade IN ('baixa','media','alta','critica')", name="ck_riscos_severidade"),
    )

    op.create_table(
        "risco_componentes",
        sa.Column("risco_id", sa.Uuid(), nullable=False),
        sa.Column("componente_id", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint("risco_id", "componente_id"),
        sa.ForeignKeyConstraint(["risco_id"], ["riscos.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["componente_id"], ["componentes.id"], ondelete="CASCADE"),
    )


def downgrade() -> None:
    op.drop_table("risco_componentes")
    op.drop_table("riscos")
    op.drop_table("componentes")
    op.drop_index("idx_processamentos_analise", table_name="processamentos")
    op.drop_table("processamentos")
