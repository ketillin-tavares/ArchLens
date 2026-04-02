import abc
import uuid

from src.domain.entities import Relatorio


class RelatorioRepository(abc.ABC):
    """Port (interface) para persistência de relatórios."""

    @abc.abstractmethod
    async def salvar(self, relatorio: Relatorio) -> Relatorio:
        """
        Persiste um relatório no repositório.

        Args:
            relatorio: Entidade Relatorio a ser salva.

        Returns:
            Relatorio persistido.
        """

    @abc.abstractmethod
    async def buscar_por_analise_id(self, analise_id: uuid.UUID) -> Relatorio | None:
        """
        Busca um relatório pelo ID da análise.

        Args:
            analise_id: ID da análise.

        Returns:
            Relatorio encontrado ou None.
        """

    @abc.abstractmethod
    async def existe_por_analise_id(self, analise_id: uuid.UUID) -> bool:
        """
        Verifica se já existe um relatório para a análise informada (idempotência).

        Args:
            analise_id: ID da análise.

        Returns:
            True se já existe, False caso contrário.
        """
