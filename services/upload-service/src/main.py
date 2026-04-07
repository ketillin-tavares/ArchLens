import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.application.use_cases import HandleStatusUpdate
from src.domain.exceptions import (
    AnaliseNaoConcluidaError,
    AnaliseNaoEncontradaError,
    ArquivoInvalidoError,
    ArquivoTamanhoExcedidoError,
    RelatorioIndisponivelError,
    RetentativaInvalidaError,
)
from src.environment import get_settings
from src.infrastructure.database import async_engine, async_session_factory
from src.infrastructure.messaging.consumer import RabbitMQConsumer
from src.infrastructure.messaging.shared import rabbitmq_publisher
from src.infrastructure.observability import MetricsRecorder, configure_logging, get_logger
from src.interface.controllers import analise_router, health_router
from src.interface.gateways.analise_repository_gateway import SQLAlchemyAnaliseRepository

logger = get_logger()


async def _status_update_handler(
    analise_id: str,
    novo_status: str,
    erro_detalhe: str | None = None,
    relatorio_s3_key: str | None = None,
) -> None:
    """Handler que processa eventos de status recebidos do RabbitMQ."""
    async with async_session_factory() as session:
        repo = SQLAlchemyAnaliseRepository(session)
        use_case = HandleStatusUpdate(analise_repository=repo)
        await use_case.execute(analise_id, novo_status, erro_detalhe, relatorio_s3_key)
        await session.commit()

    MetricsRecorder.record_analise_por_status(novo_status)
    if novo_status == "erro":
        MetricsRecorder.record_falha()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Gerencia o ciclo de vida da aplicação (startup/shutdown)."""
    settings = get_settings()
    configure_logging(settings.app.log_level)

    logger.info("upload_service_iniciando")

    await rabbitmq_publisher.connect()

    consumer = RabbitMQConsumer(status_update_handler=_status_update_handler)
    consumer_task = asyncio.create_task(consumer.start())

    logger.info("upload_service_pronto")

    yield

    logger.info("upload_service_encerrando")

    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        pass

    await consumer.close()
    await rabbitmq_publisher.close()
    await async_engine.dispose()

    logger.info("upload_service_encerrado")


app = FastAPI(
    title="upload-service",
    description="Ponto de entrada do ArchLens — recebe diagramas de arquitetura via upload",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(analise_router, prefix="/v1")
app.include_router(health_router)


@app.exception_handler(ArquivoInvalidoError)
async def arquivo_invalido_handler(request: Request, exc: ArquivoInvalidoError) -> JSONResponse:
    """Traduz ArquivoInvalidoError para HTTP 400."""
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(ArquivoTamanhoExcedidoError)
async def arquivo_tamanho_handler(request: Request, exc: ArquivoTamanhoExcedidoError) -> JSONResponse:
    """Traduz ArquivoTamanhoExcedidoError para HTTP 413."""
    return JSONResponse(status_code=413, content={"detail": str(exc)})


@app.exception_handler(AnaliseNaoEncontradaError)
async def analise_nao_encontrada_handler(request: Request, exc: AnaliseNaoEncontradaError) -> JSONResponse:
    """Traduz AnaliseNaoEncontradaError para HTTP 404."""
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(RetentativaInvalidaError)
async def retentativa_invalida_handler(request: Request, exc: RetentativaInvalidaError) -> JSONResponse:
    """Traduz RetentativaInvalidaError para HTTP 409."""
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(AnaliseNaoConcluidaError)
async def analise_nao_concluida_handler(request: Request, exc: AnaliseNaoConcluidaError) -> JSONResponse:
    """Traduz AnaliseNaoConcluidaError para HTTP 409."""
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(RelatorioIndisponivelError)
async def relatorio_indisponivel_handler(request: Request, exc: RelatorioIndisponivelError) -> JSONResponse:
    """Traduz RelatorioIndisponivelError para HTTP 404."""
    return JSONResponse(status_code=404, content={"detail": str(exc)})
