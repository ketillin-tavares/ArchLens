import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class ProcessamentoIniciado(BaseModel):
    """Evento emitido quando um processamento é iniciado."""

    event_type: str = Field(default="ProcessamentoIniciado")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    analise_id: uuid.UUID = Field(...)

    def to_message(self) -> dict[str, Any]:
        """Serializa o evento para publicação no RabbitMQ."""
        return {
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "payload": {"analise_id": str(self.analise_id)},
        }


class AnaliseConcluida(BaseModel):
    """Evento emitido quando uma análise é concluída com sucesso."""

    event_type: str = Field(default="AnaliseConcluida")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    analise_id: uuid.UUID = Field(...)
    componentes: list[dict[str, Any]] = Field(default_factory=list)
    riscos: list[dict[str, Any]] = Field(default_factory=list)

    def to_message(self) -> dict[str, Any]:
        """Serializa o evento para publicação no RabbitMQ."""
        return {
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "payload": {
                "analise_id": str(self.analise_id),
                "componentes": self.componentes,
                "riscos": self.riscos,
            },
        }


class AnaliseFalhou(BaseModel):
    """Evento emitido quando uma análise falha."""

    event_type: str = Field(default="AnaliseFalhou")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    analise_id: uuid.UUID = Field(...)
    erro_detalhe: str = Field(...)
    tentativa: int = Field(default=1)

    def to_message(self) -> dict[str, Any]:
        """Serializa o evento para publicação no RabbitMQ."""
        return {
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "payload": {
                "analise_id": str(self.analise_id),
                "erro_detalhe": self.erro_detalhe,
                "tentativa": self.tentativa,
            },
        }
