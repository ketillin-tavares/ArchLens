import uuid

from src.application.dtos.download_relatorio_response import DownloadRelatorioResponse
from src.application.ports import FileStorage
from src.domain.exceptions import (
    AnaliseNaoConcluidaError,
    AnaliseNaoEncontradaError,
    RelatorioIndisponivelError,
)
from src.domain.repositories import AnaliseRepository
from src.domain.value_objects import StatusAnalise
from src.infrastructure.observability.logging import get_logger

logger = get_logger()

PRESIGNED_URL_EXPIRES_IN: int = 3600


class DownloadRelatorio:
    """Caso de uso para geração de URL pré-assinada para download do relatório Markdown."""

    def __init__(
        self,
        analise_repository: AnaliseRepository,
        file_storage: FileStorage,
    ) -> None:
        self._analise_repo = analise_repository
        self._file_storage = file_storage

    async def execute(self, analise_id: uuid.UUID) -> DownloadRelatorioResponse:
        """
        Gera URL pré-assinada para download do relatório Markdown de uma análise.

        Args:
            analise_id: UUID da análise.

        Returns:
            DTO com a URL pré-assinada e metadados.

        Raises:
            AnaliseNaoEncontradaError: Se a análise não existe.
            AnaliseNaoConcluidaError: Se a análise ainda não foi concluída.
            RelatorioIndisponivelError: Se o relatório Markdown não está disponível (s3_key ausente).
        """
        analise = await self._analise_repo.buscar_por_id(analise_id)
        if analise is None:
            raise AnaliseNaoEncontradaError("Análise não encontrada")

        if analise.status != StatusAnalise.ANALISADO:
            raise AnaliseNaoConcluidaError(f"Análise ainda não concluída. Status atual: '{analise.status.value}'")

        if analise.relatorio_s3_key is None:
            logger.info("download_relatorio_indisponivel", analise_id=str(analise_id))
            raise RelatorioIndisponivelError("Relatório Markdown não disponível para esta análise")

        download_url = await self._file_storage.generate_presigned_url(
            s3_key=analise.relatorio_s3_key,
            expires_in=PRESIGNED_URL_EXPIRES_IN,
        )

        logger.info(
            "presigned_url_gerada",
            analise_id=str(analise_id),
            expires_in=PRESIGNED_URL_EXPIRES_IN,
        )

        return DownloadRelatorioResponse(
            analise_id=analise_id,
            download_url=download_url,
            expires_in_seconds=PRESIGNED_URL_EXPIRES_IN,
        )
