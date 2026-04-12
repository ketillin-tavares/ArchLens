import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.application.use_cases import ProcessDiagram
from src.domain.exceptions import ProcessamentoNaoEncontradoError
from src.environment import get_settings
from src.infrastructure.database import async_engine, async_session_factory
from src.infrastructure.messaging.consumer import RabbitMQConsumer
from src.infrastructure.messaging.shared import rabbitmq_publisher
from src.infrastructure.observability import MetricsRecorder, configure_logging, get_logger
from src.infrastructure.storage import S3StorageClient
from src.interface.controllers import health_router, processamento_router
from src.interface.gateways.analysis_pipeline_gateway import MultiAgentPipelineGateway, SingleCallPipelineGateway
from src.interface.gateways.event_publisher_gateway import RabbitMQEventPublisherGateway
from src.interface.gateways.file_storage_gateway import S3FileStorageGateway
from src.interface.gateways.image_processor_gateway import FitzImageProcessorGateway
from src.interface.gateways.llm_client_gateway import PydanticAILLMClientGateway
from src.interface.gateways.processamento_repository_gateway import SQLAlchemyProcessamentoRepository

logger = get_logger()

s3_client = S3StorageClient()


async def _diagram_handler(analise_id: str, diagrama_storage_path: str, content_type: str) -> None:
    """Handler que processa eventos DiagramaEnviado recebidos do RabbitMQ."""
    start = MetricsRecorder.start_timer()
    MetricsRecorder.record_analise_iniciada(analise_id)

    settings = get_settings()

    async with async_session_factory() as session:
        repo = SQLAlchemyProcessamentoRepository(session)
        publisher_gateway = RabbitMQEventPublisherGateway(publisher=rabbitmq_publisher)
        file_storage_gateway = S3FileStorageGateway(s3_client)
        image_processor_gateway = FitzImageProcessorGateway()

        if settings.multiagent.enable_multiagent:
            pipeline_gateway = MultiAgentPipelineGateway()
        else:
            llm_client_gateway = PydanticAILLMClientGateway()
            pipeline_gateway = SingleCallPipelineGateway(llm_client=llm_client_gateway)

        use_case = ProcessDiagram(
            processamento_repository=repo,
            event_publisher=publisher_gateway,
            file_storage=file_storage_gateway,
            image_processor=image_processor_gateway,
            analysis_pipeline=pipeline_gateway,
        )

        result = await use_case.execute(analise_id, diagrama_storage_path, content_type)
        await session.commit()

    duracao = MetricsRecorder.elapsed(start)
    MetricsRecorder.record_latency(duracao)

    if result.status == "sucesso":
        MetricsRecorder.record_component_count(result.total_componentes)
        MetricsRecorder.record_risk_count(result.total_riscos)
        MetricsRecorder.record_avg_confidence(result.avg_confianca)
        MetricsRecorder.record_analise_sucesso(analise_id, duracao, result.total_componentes, result.total_riscos)
    elif result.status == "falha":
        MetricsRecorder.record_analise_falha(analise_id, result.erro or "", result.tipo_erro or "Unknown")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Gerencia o ciclo de vida da aplicação (startup/shutdown)."""
    settings = get_settings()
    configure_logging(settings.app.log_level)

    logger.info("processing_service_iniciando")

    await rabbitmq_publisher.connect()

    consumer = RabbitMQConsumer(diagram_handler=_diagram_handler)
    consumer_task = asyncio.create_task(consumer.start())

    logger.info("processing_service_pronto")

    yield

    logger.info("processing_service_encerrando")

    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        pass

    await consumer.close()
    await rabbitmq_publisher.close()
    await async_engine.dispose()

    logger.info("processing_service_encerrado")


app = FastAPI(
    title="processing-service",
    description="Core Domain do ArchLens — analisa diagramas de arquitetura via LLM, "
    "identifica componentes e riscos arquiteturais",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(processamento_router, prefix="/v1")
app.include_router(health_router)


@app.exception_handler(ProcessamentoNaoEncontradoError)
async def processamento_nao_encontrado_handler(request: Request, exc: ProcessamentoNaoEncontradoError) -> JSONResponse:
    """Traduz ProcessamentoNaoEncontradoError para HTTP 404."""
    return JSONResponse(status_code=404, content={"detail": str(exc)})
