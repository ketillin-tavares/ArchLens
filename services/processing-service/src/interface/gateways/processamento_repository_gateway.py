import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities import Componente, Processamento, Risco, StatusProcessamento
from src.domain.repositories import ProcessamentoRepository
from src.infrastructure.models import (
    ComponenteModel,
    ProcessamentoModel,
    RiscoComponenteModel,
    RiscoModel,
)


class SQLAlchemyProcessamentoRepository(ProcessamentoRepository):
    """Adapter que implementa ProcessamentoRepository usando SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def buscar_por_analise_id(self, analise_id: uuid.UUID) -> Processamento | None:
        """
        Busca um processamento pelo ID da análise.

        Args:
            analise_id: ID da análise.

        Returns:
            Processamento encontrado ou None.
        """
        stmt = select(ProcessamentoModel).where(ProcessamentoModel.analise_id == analise_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return self._model_to_entity(model)

    async def salvar_processamento(self, processamento: Processamento) -> Processamento:
        """
        Persiste um novo processamento no banco.

        Args:
            processamento: Entidade Processamento.

        Returns:
            Processamento persistido.
        """
        model = ProcessamentoModel(
            id=processamento.id,
            analise_id=processamento.analise_id,
            status=processamento.status.value,
            tentativas=processamento.tentativas,
            iniciado_em=processamento.iniciado_em,
            concluido_em=processamento.concluido_em,
            erro_detalhe=processamento.erro_detalhe,
        )
        self._session.add(model)
        await self._session.flush()
        return processamento

    async def atualizar_processamento(self, processamento: Processamento) -> None:
        """
        Atualiza um processamento existente.

        Args:
            processamento: Entidade Processamento com dados atualizados.
        """
        stmt = select(ProcessamentoModel).where(ProcessamentoModel.id == processamento.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one()

        model.status = processamento.status.value
        model.tentativas = processamento.tentativas
        model.iniciado_em = processamento.iniciado_em
        model.concluido_em = processamento.concluido_em
        model.erro_detalhe = processamento.erro_detalhe

        await self._session.flush()

    async def salvar_componentes(self, componentes: list[Componente]) -> list[Componente]:
        """
        Persiste uma lista de componentes.

        Args:
            componentes: Lista de entidades Componente.

        Returns:
            Lista de componentes persistidos.
        """
        for comp in componentes:
            model = ComponenteModel(
                id=comp.id,
                processamento_id=comp.processamento_id,
                nome=comp.nome,
                tipo=comp.tipo,
                confianca=comp.confianca,
                metadata_=comp.metadata,
            )
            self._session.add(model)

        await self._session.flush()
        return componentes

    async def salvar_riscos(self, riscos: list[Risco], mapa_componente_ids: dict[str, uuid.UUID]) -> list[Risco]:
        """
        Persiste riscos e suas relações com componentes.

        Args:
            riscos: Lista de entidades Risco.
            mapa_componente_ids: Mapa nome_componente -> componente_id.

        Returns:
            Lista de riscos persistidos.
        """
        for risco in riscos:
            risco_model = RiscoModel(
                id=risco.id,
                processamento_id=risco.processamento_id,
                descricao=risco.descricao,
                severidade=risco.severidade,
                recomendacao_descricao=risco.recomendacao_descricao,
                recomendacao_prioridade=risco.recomendacao_prioridade,
            )
            self._session.add(risco_model)
            await self._session.flush()

            for nome_componente in risco.componentes_afetados:
                componente_id = mapa_componente_ids.get(nome_componente)
                if componente_id:
                    rel = RiscoComponenteModel(
                        risco_id=risco.id,
                        componente_id=componente_id,
                    )
                    self._session.add(rel)

        await self._session.flush()
        return riscos

    async def buscar_resultado_completo(
        self, analise_id: uuid.UUID
    ) -> tuple[Processamento | None, list[Componente], list[Risco]]:
        """
        Busca processamento com componentes e riscos associados.

        Args:
            analise_id: ID da análise.

        Returns:
            Tupla (processamento, componentes, riscos).
        """
        stmt = select(ProcessamentoModel).where(ProcessamentoModel.analise_id == analise_id)
        result = await self._session.execute(stmt)
        proc_model = result.scalar_one_or_none()

        if proc_model is None:
            return None, [], []

        processamento = self._model_to_entity(proc_model)

        comp_stmt = select(ComponenteModel).where(ComponenteModel.processamento_id == proc_model.id)
        comp_result = await self._session.execute(comp_stmt)
        comp_models = comp_result.scalars().all()

        componentes = [
            Componente(
                id=m.id,
                processamento_id=m.processamento_id,
                nome=m.nome,
                tipo=m.tipo,
                confianca=m.confianca,
                metadata=m.metadata_,
            )
            for m in comp_models
        ]

        mapa_comp_nomes: dict[uuid.UUID, str] = {m.id: m.nome for m in comp_models}

        risco_stmt = select(RiscoModel).where(RiscoModel.processamento_id == proc_model.id)
        risco_result = await self._session.execute(risco_stmt)
        risco_models = risco_result.scalars().all()

        riscos: list[Risco] = []
        for rm in risco_models:
            rel_stmt = select(RiscoComponenteModel).where(RiscoComponenteModel.risco_id == rm.id)
            rel_result = await self._session.execute(rel_stmt)
            rel_models = rel_result.scalars().all()
            nomes_afetados = [
                mapa_comp_nomes[r.componente_id] for r in rel_models if r.componente_id in mapa_comp_nomes
            ]

            riscos.append(
                Risco(
                    id=rm.id,
                    processamento_id=rm.processamento_id,
                    descricao=rm.descricao,
                    severidade=rm.severidade,
                    recomendacao_descricao=rm.recomendacao_descricao,
                    recomendacao_prioridade=rm.recomendacao_prioridade,
                    componentes_afetados=nomes_afetados,
                )
            )

        return processamento, componentes, riscos

    @staticmethod
    def _model_to_entity(model: ProcessamentoModel) -> Processamento:
        """Converte ProcessamentoModel para entidade Processamento."""
        return Processamento(
            id=model.id,
            analise_id=model.analise_id,
            status=StatusProcessamento(model.status),
            tentativas=model.tentativas,
            iniciado_em=model.iniciado_em,
            concluido_em=model.concluido_em,
            erro_detalhe=model.erro_detalhe,
        )
