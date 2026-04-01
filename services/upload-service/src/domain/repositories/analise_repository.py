import abc
import uuid

from src.domain.entities import Analise
from src.domain.value_objects import StatusAnalise


class AnaliseRepository(abc.ABC):
    """Port (interface) para persistência de análises."""

    @abc.abstractmethod
    async def salvar(self, analise: Analise) -> Analise:
        """
        Persiste uma análise no repositório.

        Args:
            analise: Entidade Analise a ser salva.

        Returns:
            Analise persistida com ID gerado.
        """

    @abc.abstractmethod
    async def buscar_por_id(self, analise_id: uuid.UUID) -> Analise | None:
        """
        Busca uma análise pelo ID.

        Args:
            analise_id: ID da análise.

        Returns:
            Analise encontrada ou None.
        """

    @abc.abstractmethod
    async def atualizar_status(
        self, analise_id: uuid.UUID, novo_status: StatusAnalise, erro_detalhe: str | None = None
    ) -> bool:
        """
        Atualiza o status de uma análise de forma idempotente.

        Args:
            analise_id: ID da análise.
            novo_status: Novo status a ser aplicado.
            erro_detalhe: Detalhes do erro (para status ERRO).

        Returns:
            True se o status foi atualizado, False se foi ignorado.
        """
