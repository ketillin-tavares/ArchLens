import uuid

from src.application.dtos import AnaliseResponse
from src.application.ports import EventPublisher
from src.domain.events import DiagramaEnviado
from src.domain.exceptions import AnaliseNaoEncontradaError
from src.domain.repositories import AnaliseRepository, DiagramaRepository
from src.infrastructure.observability.logging import get_logger

logger = get_logger()


class RetryAnalysis:
    """Caso de uso para retentativa de processamento de uma análise que falhou."""

    def __init__(
        self,
        analise_repository: AnaliseRepository,
        diagrama_repository: DiagramaRepository,
        event_publisher: EventPublisher,
    ) -> None:
        self._analise_repo = analise_repository
        self._diagrama_repo = diagrama_repository
        self._event_publisher = event_publisher

    async def execute(self, analise_id: uuid.UUID) -> AnaliseResponse:
        """
        Retenta o processamento de uma análise com status ERRO.

        Args:
            analise_id: UUID da análise a ser retentada.

        Returns:
            DTO com os dados da análise resetada.

        Raises:
            AnaliseNaoEncontradaError: Se a análise não existe.
            RetentativaInvalidaError: Se o status não é ERRO.
        """
        analise = await self._analise_repo.buscar_por_id(analise_id)
        if analise is None:
            raise AnaliseNaoEncontradaError("Análise não encontrada")

        analise.resetar_para_retentativa()

        await self._analise_repo.resetar_para_retentativa(analise.id)

        diagrama = await self._diagrama_repo.buscar_por_id(analise.diagrama_id)
        if diagrama is None:
            raise AnaliseNaoEncontradaError("Diagrama associado não encontrado")

        logger.info(
            "retentativa_analise_solicitada",
            analise_id=str(analise.id),
            diagrama_id=str(analise.diagrama_id),
        )

        evento = DiagramaEnviado(
            analise_id=analise.id,
            diagrama_storage_path=diagrama.storage_path,
            content_type=diagrama.content_type,
            tamanho_bytes=diagrama.tamanho_bytes,
        )
        await self._event_publisher.publish_event(
            event_type=evento.event_type,
            routing_key="analise.diagrama.enviado",
            payload=evento.to_message(),
        )

        return AnaliseResponse(
            id=analise.id,
            diagrama_id=analise.diagrama_id,
            status=analise.status.value,
            erro_detalhe=analise.erro_detalhe,
            relatorio_s3_key=analise.relatorio_s3_key,
            criado_em=analise.criado_em,
            atualizado_em=analise.atualizado_em,
        )
