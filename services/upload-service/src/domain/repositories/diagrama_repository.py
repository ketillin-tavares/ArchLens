import abc
import uuid

from src.domain.entities import Diagrama


class DiagramaRepository(abc.ABC):
    """Port (interface) para persistência de diagramas."""

    @abc.abstractmethod
    async def salvar(self, diagrama: Diagrama) -> Diagrama:
        """
        Persiste um diagrama no repositório.

        Args:
            diagrama: Entidade Diagrama a ser salva.

        Returns:
            Diagrama persistido com ID gerado.
        """

    @abc.abstractmethod
    async def buscar_por_id(self, diagrama_id: uuid.UUID) -> Diagrama | None:
        """
        Busca um diagrama pelo ID.

        Args:
            diagrama_id: ID do diagrama.

        Returns:
            Diagrama encontrado ou None.
        """
