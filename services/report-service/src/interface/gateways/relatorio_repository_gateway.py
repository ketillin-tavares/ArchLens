import uuid

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities import Relatorio
from src.domain.repositories import RelatorioRepository
from src.infrastructure.models.relatorio_model import RelatorioModel


class SQLAlchemyRelatorioRepository(RelatorioRepository):
    """Adapter que implementa RelatorioRepository usando SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def salvar(self, relatorio: Relatorio) -> Relatorio:
        """
        Persiste um relatório no banco de dados.

        Args:
            relatorio: Entidade Relatorio a ser salva.

        Returns:
            Relatorio persistido.
        """
        model = RelatorioModel(
            id=relatorio.id,
            analise_id=relatorio.analise_id,
            titulo=relatorio.titulo,
            resumo=relatorio.resumo,
            conteudo=relatorio.conteudo,
            s3_key=relatorio.s3_key,
            criado_em=relatorio.criado_em,
        )
        self._session.add(model)
        await self._session.flush()
        return relatorio

    async def buscar_por_analise_id(self, analise_id: uuid.UUID) -> Relatorio | None:
        """
        Busca um relatório pelo ID da análise.

        Args:
            analise_id: ID da análise.

        Returns:
            Relatorio encontrado ou None.
        """
        stmt = select(RelatorioModel).where(RelatorioModel.analise_id == analise_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return Relatorio(
            id=model.id,
            analise_id=model.analise_id,
            titulo=model.titulo or "",
            resumo=model.resumo or "",
            conteudo=model.conteudo,
            s3_key=model.s3_key,
            criado_em=model.criado_em,
        )

    async def existe_por_analise_id(self, analise_id: uuid.UUID) -> bool:
        """
        Verifica se já existe um relatório para a análise informada.

        Args:
            analise_id: ID da análise.

        Returns:
            True se já existe, False caso contrário.
        """
        stmt = select(exists().where(RelatorioModel.analise_id == analise_id))
        result = await self._session.execute(stmt)
        return result.scalar() or False
