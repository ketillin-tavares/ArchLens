import uuid

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.models.base import Base


class RiscoModel(Base):
    """Modelo ORM para a tabela riscos."""

    __tablename__ = "riscos"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    processamento_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    severidade: Mapped[str] = mapped_column(String(10), nullable=False)
    recomendacao_descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
    recomendacao_prioridade: Mapped[str | None] = mapped_column(String(10), nullable=True)
