import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.application.use_cases import GenerateReport
from src.domain.exceptions import RelatorioNaoEncontradoError
from src.environment import get_settings
from src.infrastructure.database import async_engine, async_session_factory
from src.infrastructure.messaging.consumer import RabbitMQConsumer
from src.infrastructure.messaging.shared import rabbitmq_publisher
from src.infrastructure.observability import MetricsRecorder, configure_logging
from src.interface.controllers import health_router, relatorio_router
from src.interface.gateways.event_publisher_gateway import RabbitMQEventPublisherGateway
from src.interface.gateways.relatorio_repository_gateway import SQLAlchemyRelatorioRepository

logger = structlog.get_logger()


async def _report_handler(analise_id: str, componentes: list[dict[str, Any]], riscos: list[dict[str, Any]]) -> None:
    """Handler que processa eventos AnaliseConcluida recebidos do RabbitMQ."""
    start = MetricsRecorder.start_timer()

    async with async_session_factory() as session:
        repo = SQLAlchemyRelatorioRepository(session)
        publisher_gateway = RabbitMQEventPublisherGateway(publisher=rabbitmq_publisher)
        use_case = GenerateReport(relatorio_repository=repo, event_publisher=publisher_gateway)
        await use_case.execute(analise_id, componentes, riscos)
        await session.commit()

    duracao = MetricsRecorder.elapsed(start)
    MetricsRecorder.record_relatorio_gerado()
    MetricsRecorder.record_tempo_geracao(analise_id, duracao)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Gerencia o ciclo de vida da aplicação (startup/shutdown)."""
    settings = get_settings()
    configure_logging(settings.app.log_level)

    logger.info("report_service_iniciando")

    await rabbitmq_publisher.connect()

    consumer = RabbitMQConsumer(report_handler=_report_handler)
    consumer_task = asyncio.create_task(consumer.start())

    logger.info("report_service_pronto")

    yield

    logger.info("report_service_encerrando")

    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        pass

    await consumer.close()
    await rabbitmq_publisher.close()
    await async_engine.dispose()

    logger.info("report_service_encerrado")


app = FastAPI(
    title="report-service",
    description="Serviço de geração de relatórios do ArchLens — consome eventos de análise concluída"
    "e gera relatórios estruturados",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(relatorio_router, prefix="/v1")
app.include_router(health_router)


@app.exception_handler(RelatorioNaoEncontradoError)
async def relatorio_nao_encontrado_handler(request: Request, exc: RelatorioNaoEncontradoError) -> JSONResponse:
    """Traduz RelatorioNaoEncontradoError para HTTP 404."""
    return JSONResponse(status_code=404, content={"detail": str(exc)})
