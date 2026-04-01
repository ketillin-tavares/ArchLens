import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, Field


class DiagramaEnviado(BaseModel):
    """Evento de domínio publicado quando um diagrama é recebido e armazenado com sucesso."""

    event_type: str = Field(default="DiagramaEnviado", description="Tipo do evento")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Momento do evento")
    analise_id: uuid.UUID = Field(..., description="ID da análise criada")
    diagrama_storage_path: str = Field(..., description="Caminho do diagrama no S3")
    content_type: str = Field(..., description="MIME type do diagrama")
    tamanho_bytes: int = Field(..., gt=0, description="Tamanho do arquivo em bytes")

    def to_message(self) -> dict:
        """Serializa o evento para publicação no RabbitMQ."""
        return {
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "payload": {
                "analise_id": str(self.analise_id),
                "diagrama_storage_path": self.diagrama_storage_path,
                "content_type": self.content_type,
                "tamanho_bytes": self.tamanho_bytes,
            },
        }
