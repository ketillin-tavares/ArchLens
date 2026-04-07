"""Fixtures and configuration for pytest."""

import uuid
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from src.application.ports import EventPublisher, FileStorage, MarkdownReportWriter
from src.domain.entities import Relatorio
from src.domain.repositories import RelatorioRepository
from src.main import app


@pytest.fixture
def analise_id() -> uuid.UUID:
    """Fixture para UUID de análise."""
    return uuid.uuid4()


@pytest.fixture
def relatorio_id() -> uuid.UUID:
    """Fixture para UUID de relatório."""
    return uuid.uuid4()


@pytest.fixture
def mock_relatorio_repository() -> RelatorioRepository:
    """Fixture com mock da interface RelatorioRepository."""
    repo = AsyncMock(spec=RelatorioRepository)
    return repo


@pytest.fixture
def mock_event_publisher() -> EventPublisher:
    """Fixture com mock da interface EventPublisher."""
    publisher = AsyncMock(spec=EventPublisher)
    return publisher


@pytest.fixture
def mock_markdown_report_writer() -> MarkdownReportWriter:
    """Fixture com mock da interface MarkdownReportWriter."""
    writer = AsyncMock(spec=MarkdownReportWriter)
    return writer


@pytest.fixture
def mock_file_storage() -> FileStorage:
    """Fixture com mock da interface FileStorage."""
    storage = AsyncMock(spec=FileStorage)
    return storage


@pytest.fixture
def sample_relatorio(analise_id: uuid.UUID, relatorio_id: uuid.UUID) -> Relatorio:
    """Fixture com uma entidade Relatorio de exemplo."""
    return Relatorio(
        id=relatorio_id,
        analise_id=analise_id,
        titulo="Análise Arquitetural - 2026-04-01",
        resumo="Foram identificados 5 componentes arquiteturais e 3 riscos (1 crítico(s), 1 alto(s), 1 médio(s)).",
        conteudo={
            "componentes": [
                {"id": "comp_1", "nome": "API Gateway"},
                {"id": "comp_2", "nome": "Auth Service"},
                {"id": "comp_3", "nome": "Database"},
                {"id": "comp_4", "nome": "Cache"},
                {"id": "comp_5", "nome": "Message Queue"},
            ],
            "riscos": [
                {"id": "risk_1", "severidade": "critica", "descricao": "Critical issue"},
                {"id": "risk_2", "severidade": "alta", "descricao": "High issue"},
                {"id": "risk_3", "severidade": "media", "descricao": "Medium issue"},
            ],
            "estatisticas": {
                "total_componentes": 5,
                "total_riscos": 3,
                "riscos_por_severidade": {
                    "critica": 1,
                    "alta": 1,
                    "media": 1,
                    "baixa": 0,
                },
            },
        },
        s3_key=f"relatorios/{analise_id}.md",
        criado_em=datetime.now(UTC),
    )


@pytest.fixture
def sample_componentes() -> list[dict[str, Any]]:
    """Fixture com lista de componentes de exemplo."""
    return [
        {"id": "comp_1", "nome": "API Gateway", "tipo": "gateway"},
        {"id": "comp_2", "nome": "Auth Service", "tipo": "service"},
        {"id": "comp_3", "nome": "Database", "tipo": "database"},
        {"id": "comp_4", "nome": "Cache", "tipo": "cache"},
        {"id": "comp_5", "nome": "Message Queue", "tipo": "message_broker"},
    ]


@pytest.fixture
def sample_riscos() -> list[dict[str, Any]]:
    """Fixture com lista de riscos de exemplo."""
    return [
        {"id": "risk_1", "severidade": "critica", "descricao": "Critical security issue"},
        {"id": "risk_2", "severidade": "alta", "descricao": "High performance issue"},
        {"id": "risk_3", "severidade": "media", "descricao": "Medium scalability issue"},
    ]


@pytest.fixture
async def async_client() -> AsyncClient:
    """Fixture para cliente HTTP assíncrono."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def sync_client() -> TestClient:
    """Fixture para cliente HTTP síncrono (não assíncrono)."""
    return TestClient(app)
