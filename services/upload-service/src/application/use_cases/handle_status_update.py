import uuid

from src.domain.repositories import AnaliseRepository
from src.domain.value_objects import StatusAnalise
from src.infrastructure.observability.logging import get_logger

logger = get_logger()


class HandleStatusUpdate:
    """Caso de uso para atualização de status de análise via eventos RabbitMQ."""

    def __init__(self, analise_repository: AnaliseRepository) -> None:
        self._analise_repo = analise_repository

    async def execute(
        self,
        analise_id: str,
        novo_status: str,
        erro_detalhe: str | None = None,
        relatorio_s3_key: str | None = None,
    ) -> None:
        """
        Atualiza o status de uma análise baseado em evento recebido.

        Args:
            analise_id: UUID da análise (como string).
            novo_status: Novo status a aplicar.
            erro_detalhe: Detalhes do erro (para status 'erro').
            relatorio_s3_key: Chave S3 do relatório Markdown (para status 'analisado').
        """
        try:
            uid = uuid.UUID(analise_id)
            status = StatusAnalise(novo_status)
        except (ValueError, KeyError):
            logger.error("evento_invalido", analise_id=analise_id, novo_status=novo_status)
            return

        analise = await self._analise_repo.buscar_por_id(uid)
        if analise is None:
            logger.warning("analise_nao_encontrada_para_evento", analise_id=analise_id)
            return

        status_anterior = analise.status.value
        atualizado = await self._analise_repo.atualizar_status(uid, status, erro_detalhe, relatorio_s3_key)

        if atualizado:
            if relatorio_s3_key:
                logger.info("relatorio_s3_key_salvo", analise_id=analise_id, s3_key=relatorio_s3_key)
            logger.info(
                "status_atualizado",
                analise_id=analise_id,
                status_anterior=status_anterior,
                status_novo=novo_status,
            )
        else:
            logger.debug(
                "status_nao_atualizado_idempotencia",
                analise_id=analise_id,
                status_atual=status_anterior,
                status_tentado=novo_status,
            )
