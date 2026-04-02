import aio_pika
from fastapi import APIRouter
from sqlalchemy import text

from src.environment import get_settings
from src.infrastructure.database import async_engine
from src.interface.presenters.health_presenter import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Verifica a saúde do serviço e suas dependências.

    Testa conexão com banco de dados e RabbitMQ.
    """
    db_status = await _check_database()
    rabbitmq_status = await _check_rabbitmq()

    return HealthResponse(
        status="healthy",
        service="report-service",
        dependencies={
            "database": db_status,
            "rabbitmq": rabbitmq_status,
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
