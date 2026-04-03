import uuid

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.models.base import Base


class RiscoComponenteModel(Base):
    """Modelo ORM para a tabela risco_componentes (relação N:M)."""

    __tablename__ = "risco_componentes"

    risco_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    componente_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
