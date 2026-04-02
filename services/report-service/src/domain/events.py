import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, Field


class RelatorioGerado(BaseModel):
    """Evento de domínio publicado quando um relatório é gerado com sucesso."""

    event_type: str = Field(default="RelatorioGerado", description="Tipo do evento")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Momento do evento")
    analise_id: uuid.UUID = Field(..., description="ID da análise")
    relatorio_id: uuid.UUID = Field(..., description="ID do relatório gerado")

    def to_message(self) -> dict:
        """Serializa o evento para publicação no RabbitMQ."""
        return {
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "payload": {
                "analise_id": str(self.analise_id),
                "relatorio_id": str(self.relatorio_id),
            },
        }
