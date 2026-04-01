import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.models.base import Base

if TYPE_CHECKING:
    from src.infrastructure.models.analise_model import AnaliseModel


class DiagramaModel(Base):
    """Modelo ORM para a tabela diagramas."""

    __tablename__ = "diagramas"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    nome_original: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)
    tamanho_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    analises: Mapped[list["AnaliseModel"]] = relationship(back_populates="diagrama", cascade="all, delete-orphan")
