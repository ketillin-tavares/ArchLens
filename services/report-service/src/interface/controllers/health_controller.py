import aio_pika
import httpx
from fastapi import APIRouter
from sqlalchemy import text

from src.environment import get_settings
from src.infrastructure.database import async_engine
from src.infrastructure.storage.s3_client import S3StorageClient
from src.interface.presenters.health_presenter import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Verifica a saúde do serviço e suas dependências.

    Testa conexão com banco de dados, RabbitMQ, S3 e LiteLLM Proxy.
    """
    db_status = await _check_database()
    rabbitmq_status = await _check_rabbitmq()
    s3_status = await _check_s3()
    llm_status = await _check_llm_api()

    return HealthResponse(
        status="healthy",
        service="report-service",
        dependencies={
            "database": db_status,
            "rabbitmq": rabbitmq_status,
            "s3": s3_status,
            "llm_api": llm_status,
        },
    )


async def _check_database() -> str:
    """Verifica conexão com o banco de dados executando SELECT 1."""
    try:
        async with async_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return "ok"
    except Exception:
        return "degraded"


async def _check_rabbitmq() -> str:
    """Verifica conexão com o RabbitMQ."""
    try:
        settings = get_settings()
        connection = await aio_pika.connect_robust(settings.rabbitmq.url, timeout=5)
        await connection.close()
        return "ok"
    except Exception:
        return "degraded"


async def _check_s3() -> str:
    """Verifica acesso ao bucket S3."""
    try:
        client = S3StorageClient()
        is_healthy = await client.check_health()
        return "ok" if is_healthy else "degraded"
    except Exception:
        return "degraded"


async def _check_llm_api() -> str:
    """Verifica se o LiteLLM Proxy responde em /health/readiness."""
    try:
        settings = get_settings()
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.llm.base_url}/health/readiness")
            if response.status_code == 200:
                return "ok"
            return "degraded"
    except Exception:
        return "degraded"
