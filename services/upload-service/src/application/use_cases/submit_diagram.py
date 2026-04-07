import uuid
from datetime import UTC, datetime

from src.application.dtos import DiagramaUploadResponse
from src.application.ports import EventPublisher, FileStorage
from src.domain.entities import Analise, Diagrama
from src.domain.events import DiagramaEnviado
from src.domain.repositories import AnaliseRepository, DiagramaRepository
from src.domain.value_objects import ArquivoDiagrama, StatusAnalise
from src.infrastructure.observability.logging import get_logger

logger = get_logger()


class SubmitDiagram:
    """Caso de uso para submissão de um diagrama de arquitetura."""

    def __init__(
        self,
        diagrama_repository: DiagramaRepository,
        analise_repository: AnaliseRepository,
        file_storage: FileStorage,
        event_publisher: EventPublisher,
    ) -> None:
        self._diagrama_repo = diagrama_repository
        self._analise_repo = analise_repository
        self._file_storage = file_storage
        self._event_publisher = event_publisher

    async def execute(self, arquivo: ArquivoDiagrama) -> DiagramaUploadResponse:
        """
        Executa o fluxo de submissão de diagrama.

        Args:
            arquivo: Value object com os dados do arquivo enviado.

        Returns:
            DTO com os dados da análise criada.

        Raises:
            ArquivoInvalidoError: Se o tipo de arquivo não é suportado.
            ArquivoTamanhoExcedidoError: Se o arquivo excede o tamanho máximo.
        """
        arquivo.validar()

        diagrama_id = uuid.uuid4()
        now = datetime.now(UTC)
        storage_path = f"diagramas/{now.year}/{now.month:02d}/{now.day:02d}/{diagrama_id}.{arquivo.extensao}"

        await self._file_storage.upload_file(
            file_bytes=arquivo.conteudo,
            storage_path=storage_path,
            content_type=arquivo.content_type,
        )

        diagrama = Diagrama(
            id=diagrama_id,
            nome_original=arquivo.nome_original,
            content_type=arquivo.content_type,
            tamanho_bytes=arquivo.tamanho_bytes,
            storage_path=storage_path,
            criado_em=now,
        )
        await self._diagrama_repo.salvar(diagrama)

        analise = Analise(
            diagrama_id=diagrama.id,
            status=StatusAnalise.RECEBIDO,
            criado_em=now,
            atualizado_em=now,
        )
        analise = await self._analise_repo.salvar(analise)

        logger.info(
            "diagrama_recebido",
            analise_id=str(analise.id),
            content_type=arquivo.content_type,
            tamanho_bytes=arquivo.tamanho_bytes,
        )

        evento = DiagramaEnviado(
            analise_id=analise.id,
            diagrama_storage_path=storage_path,
            content_type=arquivo.content_type,
            tamanho_bytes=arquivo.tamanho_bytes,
            timestamp=now,
        )
        await self._event_publisher.publish_event(
            event_type=evento.event_type,
            routing_key="analise.diagrama.enviado",
            payload=evento.to_message(),
        )

        return DiagramaUploadResponse(
            analise_id=analise.id,
            status=analise.status.value,
            criado_em=analise.criado_em,
        )
