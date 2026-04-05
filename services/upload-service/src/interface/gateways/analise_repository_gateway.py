import uuid
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities import Analise
from src.domain.repositories import AnaliseRepository
from src.domain.value_objects import StatusAnalise
from src.infrastructure.models.analise_model import AnaliseModel

STATUS_ORDER: dict[str, int] = {
    "recebido": 0,
    "em_processamento": 1,
    "analisado": 2,
    "erro": 2,
}


class SQLAlchemyAnaliseRepository(AnaliseRepository):
    """Adapter que implementa AnaliseRepository usando SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def salvar(self, analise: Analise) -> Analise:
        """
        Persiste uma análise no banco de dados.

        Args:
            analise: Entidade Analise a ser salva.

        Returns:
            Analise persistida.
        """
        model = AnaliseModel(
            id=analise.id,
            diagrama_id=analise.diagrama_id,
            status=analise.status.value,
            erro_detalhe=analise.erro_detalhe,
            criado_em=analise.criado_em,
            atualizado_em=analise.atualizado_em,
        )
        self._session.add(model)
        await self._session.flush()
        return analise

    async def buscar_por_id(self, analise_id: uuid.UUID) -> Analise | None:
        """
        Busca uma análise pelo ID.

        Args:
            analise_id: ID da análise.

        Returns:
            Analise encontrada ou None.
        """
        stmt = select(AnaliseModel).where(AnaliseModel.id == analise_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return Analise(
            id=model.id,
            diagrama_id=model.diagrama_id,
            status=StatusAnalise(model.status),
            erro_detalhe=model.erro_detalhe,
            criado_em=model.criado_em,
            atualizado_em=model.atualizado_em,
        )

    async def atualizar_status(
        self, analise_id: uuid.UUID, novo_status: StatusAnalise, erro_detalhe: str | None = None
    ) -> bool:
        """
        Atualiza o status de uma análise de forma idempotente (não regredir).

        Args:
            analise_id: ID da análise.
            novo_status: Novo status a ser aplicado.
            erro_detalhe: Detalhes do erro (para status ERRO).

        Returns:
            True se atualizado, False se ignorado por idempotência.
        """
        analise = await self.buscar_por_id(analise_id)
        if analise is None:
            return False

        if not analise.status.pode_transitar_para(novo_status):
            return False

        values: dict = {
            "status": novo_status.value,
            "atualizado_em": datetime.now(UTC),
        }
        if novo_status == StatusAnalise.ERRO and erro_detalhe:
            values["erro_detalhe"] = erro_detalhe

        stmt = update(AnaliseModel).where(AnaliseModel.id == analise_id).values(**values)
        await self._session.execute(stmt)
        await self._session.flush()
        return True

    async def resetar_para_retentativa(self, analise_id: uuid.UUID) -> None:
        """
        Reseta uma análise para retentativa, voltando ao status RECEBIDO.

        Args:
            analise_id: ID da análise a ser resetada.
        """
        stmt = (
            update(AnaliseModel)
            .where(AnaliseModel.id == analise_id)
            .values(
                status=StatusAnalise.RECEBIDO.value,
                erro_detalhe=None,
                atualizado_em=datetime.now(UTC),
            )
        )
        await self._session.execute(stmt)
        await self._session.flush()
