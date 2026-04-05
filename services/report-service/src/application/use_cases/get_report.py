import uuid

import structlog

from src.application.dtos import RelatorioResponse
from src.domain.exceptions import RelatorioNaoEncontradoError
from src.domain.repositories import RelatorioRepository

logger = structlog.get_logger()


class GetReport:
    """Caso de uso para consulta de um relatório por análise ID."""

    def __init__(self, relatorio_repository: RelatorioRepository) -> None:
        self._relatorio_repo = relatorio_repository

    async def execute(self, analise_id: uuid.UUID) -> RelatorioResponse:
        """
        Busca o relatório associado a uma análise.

        Args:
            analise_id: UUID da análise.

        Returns:
            DTO com os dados do relatório.

        Raises:
            RelatorioNaoEncontradoError: Se não existe relatório para a análise.
        """
        relatorio = await self._relatorio_repo.buscar_por_analise_id(analise_id)
        if relatorio is None:
            logger.info("relatorio_nao_encontrado", analise_id=str(analise_id))
            raise RelatorioNaoEncontradoError("Relatório ainda não gerado para esta análise")

        logger.info("relatorio_consultado", analise_id=str(analise_id))

        return RelatorioResponse(
            id=relatorio.id,
            analise_id=relatorio.analise_id,
            titulo=relatorio.titulo,
            resumo=relatorio.resumo,
            conteudo=relatorio.conteudo,
            s3_key=relatorio.s3_key,
            criado_em=relatorio.criado_em,
        )
