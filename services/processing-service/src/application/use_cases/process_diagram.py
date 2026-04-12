import uuid

from src.application.dtos.process_diagram_result import ProcessDiagramResult
from src.application.ports import AnalysisPipeline, EventPublisher, FileStorage, ImageProcessor
from src.domain.entities import Componente, Processamento, Risco, StatusProcessamento
from src.domain.events import AnaliseConcluida, AnaliseFalhou, ProcessamentoIniciado
from src.domain.exceptions import (
    AnaliseInsanaError,
    ImageProcessingError,
    LLMApiError,
    LLMContentFilterError,
    LLMContextWindowError,
    SchemaValidationError,
    StorageDownloadError,
)
from src.domain.repositories import ProcessamentoRepository
from src.infrastructure.observability.logging import get_logger

logger = get_logger()

NON_RETRIABLE_EXCEPTIONS = (LLMContentFilterError, LLMContextWindowError, AnaliseInsanaError, ImageProcessingError)
RETRIABLE_EXCEPTIONS = (LLMApiError, StorageDownloadError)


class ProcessDiagram:
    """Caso de uso principal: consome DiagramaEnviado e executa o pipeline de análise."""

    def __init__(
        self,
        processamento_repository: ProcessamentoRepository,
        event_publisher: EventPublisher,
        file_storage: FileStorage,
        image_processor: ImageProcessor,
        analysis_pipeline: AnalysisPipeline,
    ) -> None:
        self._repo = processamento_repository
        self._event_publisher = event_publisher
        self._file_storage = file_storage
        self._image_processor = image_processor
        self._analysis_pipeline = analysis_pipeline

    async def execute(self, analise_id: str, diagrama_storage_path: str, content_type: str) -> ProcessDiagramResult:
        """
        Executa o pipeline completo de análise de diagrama.

        Args:
            analise_id: ID da análise (string UUID).
            diagrama_storage_path: Caminho do diagrama no S3.
            content_type: MIME type do arquivo.

        Returns:
            ProcessDiagramResult com status, contagens e métricas do processamento.
        """
        analise_uuid = uuid.UUID(analise_id)

        existing = await self._repo.buscar_por_analise_id(analise_uuid)
        if existing and existing.status == StatusProcessamento.CONCLUIDO:
            logger.info("processamento_duplicado_ignorado", analise_id=analise_id)
            return ProcessDiagramResult(status="duplicado")

        processamento = Processamento(analise_id=analise_uuid)
        processamento.iniciar()

        if existing and existing.status == StatusProcessamento.ERRO:
            processamento = existing
            processamento.iniciar()
            await self._repo.atualizar_processamento(processamento)
        else:
            processamento = await self._repo.salvar_processamento(processamento)

        evento_iniciado = ProcessamentoIniciado(analise_id=analise_uuid)
        await self._event_publisher.publish_event(
            event_type=evento_iniciado.event_type,
            routing_key="analise.processamento.iniciado",
            payload=evento_iniciado.to_message(),
        )

        try:
            resultado = await self._run_pipeline(processamento, diagrama_storage_path, content_type)
            await self._persist_results(processamento, resultado)

            processamento.concluir()
            await self._repo.atualizar_processamento(processamento)

            componentes: list[Componente] = resultado["componentes"]
            riscos: list[Risco] = resultado["riscos"]

            evento_concluida = AnaliseConcluida(
                analise_id=analise_uuid,
                componentes=[c.model_dump(mode="json") for c in componentes],
                riscos=[r.model_dump(mode="json") for r in riscos],
            )
            await self._event_publisher.publish_event(
                event_type=evento_concluida.event_type,
                routing_key="analise.processamento.concluida",
                payload=evento_concluida.to_message(),
            )

            total_componentes = len(componentes)
            total_riscos = len(riscos)
            avg_confianca = sum(c.confianca for c in componentes) / total_componentes if componentes else 0.0

            logger.info(
                "analise_concluida",
                analise_id=analise_id,
                total_componentes=total_componentes,
                total_riscos=total_riscos,
            )

            return ProcessDiagramResult(
                status="sucesso",
                total_componentes=total_componentes,
                total_riscos=total_riscos,
                avg_confianca=avg_confianca,
            )

        except NON_RETRIABLE_EXCEPTIONS as exc:
            await self._handle_failure(processamento, str(exc), tentativa=1)
            return ProcessDiagramResult(status="falha", erro=str(exc), tipo_erro=type(exc).__name__)
        except RETRIABLE_EXCEPTIONS as exc:
            await self._handle_failure(processamento, str(exc), tentativa=processamento.tentativas)
            return ProcessDiagramResult(status="falha", erro=str(exc), tipo_erro=type(exc).__name__)
        except SchemaValidationError as exc:
            await self._handle_failure(processamento, str(exc), tentativa=processamento.tentativas)
            return ProcessDiagramResult(status="falha", erro=str(exc), tipo_erro=type(exc).__name__)
        except Exception as exc:
            logger.exception("erro_inesperado_pipeline", analise_id=analise_id)
            await self._handle_failure(processamento, f"Erro interno inesperado: {exc}", tentativa=1)
            return ProcessDiagramResult(status="falha", erro=str(exc), tipo_erro=type(exc).__name__)

    async def _run_pipeline(self, processamento: Processamento, diagrama_storage_path: str, content_type: str) -> dict:
        """
        Executa as 4 etapas do pipeline de IA.

        Args:
            processamento: Entidade do processamento em curso.
            diagrama_storage_path: Caminho do diagrama no S3.
            content_type: MIME type do arquivo.

        Returns:
            Dicionário com listas de ComponenteSchema e RiscoSchema.
        """
        try:
            file_bytes = await self._file_storage.download_file(diagrama_storage_path)
        except Exception as exc:
            raise StorageDownloadError(f"Falha ao baixar diagrama: {exc}") from exc

        try:
            image_b64 = self._image_processor.normalize(file_bytes, content_type)
            logger.info("imagem_normalizada", content_type=content_type)
        except Exception as exc:
            raise ImageProcessingError(f"Falha ao normalizar imagem: {exc}") from exc

        analise_result = await self._analysis_pipeline.run(image_b64)
        logger.info(
            "pipeline_concluido",
            total_componentes=len(analise_result.componentes),
            total_riscos=len(analise_result.riscos),
        )

        componentes = [
            Componente(
                processamento_id=processamento.id,
                nome=c.nome,
                tipo=c.tipo.value,
                confianca=c.confianca,
                metadata=c.metadata.model_dump(),
            )
            for c in analise_result.componentes
        ]

        riscos = [
            Risco(
                processamento_id=processamento.id,
                descricao=r.descricao,
                severidade=r.severidade.value,
                recomendacao_descricao=r.recomendacao.descricao,
                recomendacao_prioridade=r.recomendacao.prioridade.value,
                componentes_afetados=r.componentes_afetados,
            )
            for r in analise_result.riscos
        ]

        return {"componentes": componentes, "riscos": riscos}

    async def _persist_results(self, processamento: Processamento, resultado: dict) -> None:
        """
        Persiste componentes, riscos e relações risco-componentes.

        Args:
            processamento: Processamento em curso.
            resultado: Dicionário com componentes e riscos.
        """
        componentes: list[Componente] = resultado["componentes"]
        riscos: list[Risco] = resultado["riscos"]

        saved_componentes = await self._repo.salvar_componentes(componentes)

        mapa_ids = {c.nome: c.id for c in saved_componentes}

        await self._repo.salvar_riscos(riscos, mapa_ids)

    async def _handle_failure(self, processamento: Processamento, erro_detalhe: str, tentativa: int) -> None:
        """
        Trata falha do pipeline: atualiza status e emite evento AnaliseFalhou.

        Args:
            processamento: Processamento que falhou.
            erro_detalhe: Detalhe do erro.
            tentativa: Número da tentativa.
        """
        processamento.falhar(erro_detalhe)
        await self._repo.atualizar_processamento(processamento)

        evento = AnaliseFalhou(
            analise_id=processamento.analise_id,
            erro_detalhe=erro_detalhe,
            tentativa=tentativa,
        )
        await self._event_publisher.publish_event(
            event_type=evento.event_type,
            routing_key="analise.processamento.falhou",
            payload=evento.to_message(),
        )

        logger.error(
            "analise_falhou",
            analise_id=str(processamento.analise_id),
            erro=erro_detalhe,
            tentativa=tentativa,
        )
