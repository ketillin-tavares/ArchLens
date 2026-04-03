import uuid
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class StatusProcessamento(StrEnum):
    """Status possíveis de um processamento."""

    PENDENTE = "pendente"
    EXECUTANDO = "executando"
    CONCLUIDO = "concluido"
    ERRO = "erro"


class Processamento(BaseModel):
    """Entidade que representa um processamento de análise de diagrama."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, description="Identificador único do processamento")
    analise_id: uuid.UUID = Field(..., description="ID da análise que originou o processamento")
    status: StatusProcessamento = Field(default=StatusProcessamento.PENDENTE, description="Status do processamento")
    tentativas: int = Field(default=0, description="Número de tentativas realizadas")
    iniciado_em: datetime | None = Field(default=None, description="Timestamp de início do processamento")
    concluido_em: datetime | None = Field(default=None, description="Timestamp de conclusão do processamento")
    erro_detalhe: str | None = Field(default=None, description="Detalhe do erro, se houver")

    def iniciar(self) -> None:
        """Marca o processamento como em execução."""
        self.status = StatusProcessamento.EXECUTANDO
        self.iniciado_em = datetime.now(UTC)
        self.tentativas += 1

    def concluir(self) -> None:
        """Marca o processamento como concluído com sucesso."""
        self.status = StatusProcessamento.CONCLUIDO
        self.concluido_em = datetime.now(UTC)

    def falhar(self, erro_detalhe: str) -> None:
        """Marca o processamento como erro."""
        self.status = StatusProcessamento.ERRO
        self.concluido_em = datetime.now(UTC)
        self.erro_detalhe = erro_detalhe
