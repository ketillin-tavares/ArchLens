import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, Field

from src.domain.value_objects import StatusAnalise


class Analise(BaseModel):
    """Entidade que representa uma análise de diagrama de arquitetura."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, description="Identificador único da análise")
    diagrama_id: uuid.UUID = Field(..., description="Referência ao diagrama analisado")
    status: StatusAnalise = Field(default=StatusAnalise.RECEBIDO, description="Status atual da análise")
    erro_detalhe: str | None = Field(default=None, description="Detalhes do erro, se houver")
    criado_em: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Data de criação")
    atualizado_em: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Última atualização")

    def atualizar_status(self, novo_status: StatusAnalise, erro_detalhe: str | None = None) -> bool:
        """
        Atualiza o status da análise se a transição for válida.

        Args:
            novo_status: Novo status a ser aplicado.
            erro_detalhe: Detalhes do erro (apenas para status ERRO).

        Returns:
            True se o status foi atualizado, False se a transição foi ignorada (idempotência).
        """
        if not self.status.pode_transitar_para(novo_status):
            return False

        self.status = novo_status
        self.atualizado_em = datetime.now(UTC)

        if novo_status == StatusAnalise.ERRO and erro_detalhe:
            self.erro_detalhe = erro_detalhe

        return True
