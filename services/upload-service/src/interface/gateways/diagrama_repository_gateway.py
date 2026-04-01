import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities import Diagrama
from src.domain.repositories import DiagramaRepository
from src.infrastructure.models.diagrama_model import DiagramaModel


class SQLAlchemyDiagramaRepository(DiagramaRepository):
    """Adapter que implementa DiagramaRepository usando SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def salvar(self, diagrama: Diagrama) -> Diagrama:
        """
        Persiste um diagrama no banco de dados.

        Args:
            diagrama: Entidade Diagrama a ser salva.

        Returns:
            Diagrama persistido.
        """
        model = DiagramaModel(
            id=diagrama.id,
            nome_original=diagrama.nome_original,
            content_type=diagrama.content_type,
            tamanho_bytes=diagrama.tamanho_bytes,
            storage_path=diagrama.storage_path,
            criado_em=diagrama.criado_em,
        )
        self._session.add(model)
        await self._session.flush()
        return diagrama

    async def buscar_por_id(self, diagrama_id: uuid.UUID) -> Diagrama | None:
        """
        Busca um diagrama pelo ID.

        Args:
            diagrama_id: ID do diagrama.

        Returns:
            Diagrama encontrado ou None.
        """
        stmt = select(DiagramaModel).where(DiagramaModel.id == diagrama_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return Diagrama(
            id=model.id,
            nome_original=model.nome_original,
            content_type=model.content_type,
            tamanho_bytes=model.tamanho_bytes,
            storage_path=model.storage_path,
            criado_em=model.criado_em,
        )
