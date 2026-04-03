import uuid

from sqlalchemy import Float, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.models.base import Base


class ComponenteModel(Base):
    """Modelo ORM para a tabela componentes."""

    __tablename__ = "componentes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    processamento_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    tipo: Mapped[str] = mapped_column(String(50), nullable=False)
    confianca: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)
