import uuid

from src.application.dtos import ComponenteResponse, ProcessamentoResponse, RiscoResponse
from src.domain.exceptions import ProcessamentoNaoEncontradoError
from src.domain.repositories import ProcessamentoRepository
from src.infrastructure.observability.logging import get_logger

logger = get_logger()


class GetProcessingResult:
    """Caso de uso para consulta de resultado de processamento por análise ID."""

    def __init__(self, processamento_repository: ProcessamentoRepository) -> None:
        self._repo = processamento_repository

    async def execute(self, analise_id: uuid.UUID) -> ProcessamentoResponse:
        """
        Busca o resultado de processamento para uma análise.

        Args:
            analise_id: UUID da análise.

        Returns:
            DTO com os dados do processamento e resultados.

        Raises:
            ProcessamentoNaoEncontradoError: Se não existe processamento para a análise.
        """
        processamento, componentes, riscos = await self._repo.buscar_resultado_completo(analise_id)

        if processamento is None:
            logger.info("processamento_nao_encontrado", analise_id=str(analise_id))
            raise ProcessamentoNaoEncontradoError("Processamento não encontrado para esta análise")

        logger.info("processamento_consultado", analise_id=str(analise_id))

        componentes_response = [
            ComponenteResponse(
                id=c.id,
                nome=c.nome,
                tipo=c.tipo,
                confianca=c.confianca,
                metadata=c.metadata,
            )
            for c in componentes
        ]

        riscos_response = [
            RiscoResponse(
                id=r.id,
                descricao=r.descricao,
                severidade=r.severidade,
                componentes_afetados=r.componentes_afetados,
                recomendacao={
                    "descricao": r.recomendacao_descricao or "",
                    "prioridade": r.recomendacao_prioridade or "",
                },
            )
            for r in riscos
        ]

        return ProcessamentoResponse(
            analise_id=processamento.analise_id,
            status=processamento.status.value,
            iniciado_em=processamento.iniciado_em,
            concluido_em=processamento.concluido_em,
            componentes=componentes_response,
            riscos=riscos_response,
        )
