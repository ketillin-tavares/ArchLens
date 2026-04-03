import abc
import uuid

from src.domain.entities import Componente, Processamento, Risco


class ProcessamentoRepository(abc.ABC):
    """Port (interface) para persistência de processamentos e resultados."""

    @abc.abstractmethod
    async def buscar_por_analise_id(self, analise_id: uuid.UUID) -> Processamento | None:
        """
        Busca um processamento pelo ID da análise.

        Args:
            analise_id: ID da análise.

        Returns:
            Processamento encontrado ou None.
        """

    @abc.abstractmethod
    async def salvar_processamento(self, processamento: Processamento) -> Processamento:
        """
        Persiste ou atualiza um processamento.

        Args:
            processamento: Entidade Processamento a ser salva.

        Returns:
            Processamento persistido.
        """

    @abc.abstractmethod
    async def atualizar_processamento(self, processamento: Processamento) -> None:
        """
        Atualiza um processamento existente.

        Args:
            processamento: Entidade Processamento com dados atualizados.
        """

    @abc.abstractmethod
    async def salvar_componentes(self, componentes: list[Componente]) -> list[Componente]:
        """
        Persiste uma lista de componentes.

        Args:
            componentes: Lista de entidades Componente.

        Returns:
            Lista de componentes persistidos.
        """

    @abc.abstractmethod
    async def salvar_riscos(self, riscos: list[Risco], mapa_componente_ids: dict[str, uuid.UUID]) -> list[Risco]:
        """
        Persiste uma lista de riscos e suas relações com componentes.

        Args:
            riscos: Lista de entidades Risco.
            mapa_componente_ids: Mapa nome_componente -> componente_id para risco_componentes.

        Returns:
            Lista de riscos persistidos.
        """

    @abc.abstractmethod
    async def buscar_resultado_completo(
        self, analise_id: uuid.UUID
    ) -> tuple[Processamento | None, list[Componente], list[Risco]]:
        """
        Busca processamento com componentes e riscos associados.

        Args:
            analise_id: ID da análise.

        Returns:
            Tupla (processamento, componentes, riscos). Processamento pode ser None.
        """
