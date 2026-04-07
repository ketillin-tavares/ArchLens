import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.models.base import Base


class RelatorioModel(Base):
    """Modelo ORM para a tabela relatorios."""

    __tablename__ = "relatorios"
    __table_args__ = (Index("idx_relatorios_analise", "analise_id", unique=True),)

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    analise_id: Mapped[uuid.UUID] = mapped_column(
        nullable=False,
        unique=True,
    )
    titulo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resumo: Mapped[str | None] = mapped_column(Text, nullable=True)
    conteudo: Mapped[dict] = mapped_column(JSONB, nullable=False)
    s3_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
