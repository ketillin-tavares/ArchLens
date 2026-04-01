import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.models.base import Base

if TYPE_CHECKING:
    from src.infrastructure.models.diagrama_model import DiagramaModel


class AnaliseModel(Base):
    """Modelo ORM para a tabela analises."""

    __tablename__ = "analises"
    __table_args__ = (
        CheckConstraint(
            "status IN ('recebido', 'em_processamento', 'analisado', 'erro')",
            name="ck_analises_status",
        ),
        Index("idx_analises_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    diagrama_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("diagramas.id"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="recebido",
    )
    erro_detalhe: Mapped[str | None] = mapped_column(Text, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    diagrama: Mapped["DiagramaModel"] = relationship(back_populates="analises")
