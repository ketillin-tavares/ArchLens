"""Fixtures and configuration for pytest."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from src.application.ports import AnalysisPipeline, EventPublisher, FileStorage, ImageProcessor, LLMClient
from src.domain.entities import Componente, Processamento, Risco, StatusProcessamento
from src.domain.repositories import ProcessamentoRepository
from src.domain.schemas import (
    AnaliseResultSchema,
    ComponenteMetadata,
    ComponenteSchema,
    RecomendacaoSchema,
    RiscoSchema,
    Severidade,
    TipoComponente,
)
from src.main import app


@pytest.fixture
def analise_id() -> uuid.UUID:
    """Fixture para UUID de análise."""
    return uuid.uuid4()


@pytest.fixture
def processamento_id() -> uuid.UUID:
    """Fixture para UUID de processamento."""
    return uuid.uuid4()


@pytest.fixture
def componente_id() -> uuid.UUID:
    """Fixture para UUID de componente."""
    return uuid.uuid4()


@pytest.fixture
def risco_id() -> uuid.UUID:
    """Fixture para UUID de risco."""
    return uuid.uuid4()


@pytest.fixture
def mock_processamento_repository() -> ProcessamentoRepository:
    """Fixture com mock da interface ProcessamentoRepository."""
    repo = AsyncMock(spec=ProcessamentoRepository)
    return repo


@pytest.fixture
def mock_event_publisher() -> EventPublisher:
    """Fixture com mock da interface EventPublisher."""
    publisher = AsyncMock(spec=EventPublisher)
    return publisher


@pytest.fixture
def mock_file_storage() -> FileStorage:
    """Fixture com mock da interface FileStorage."""
    storage = AsyncMock(spec=FileStorage)
    return storage


@pytest.fixture
def mock_image_processor() -> ImageProcessor:
    """Fixture com mock da interface ImageProcessor."""
    processor = MagicMock(spec=ImageProcessor)
    return processor


@pytest.fixture
def mock_llm_client() -> LLMClient:
    """Fixture com mock da interface LLMClient."""
    client = AsyncMock(spec=LLMClient)
    return client


@pytest.fixture
def mock_analysis_pipeline() -> AnalysisPipeline:
    """Fixture com mock da interface AnalysisPipeline."""
    pipeline = AsyncMock(spec=AnalysisPipeline)
    return pipeline


@pytest.fixture
def sample_processamento(analise_id: uuid.UUID, processamento_id: uuid.UUID) -> Processamento:
    """Fixture com uma entidade Processamento de exemplo."""
    return Processamento(
        id=processamento_id,
        analise_id=analise_id,
        status=StatusProcessamento.PENDENTE,
        tentativas=0,
        iniciado_em=None,
        concluido_em=None,
        erro_detalhe=None,
    )


@pytest.fixture
def sample_componente(processamento_id: uuid.UUID, componente_id: uuid.UUID) -> Componente:
    """Fixture com uma entidade Componente de exemplo."""
    return Componente(
        id=componente_id,
        processamento_id=processamento_id,
        nome="API Gateway",
        tipo="api_gateway",
        confianca=0.95,
        metadata={"descricao": "API Gateway da aplicação"},
    )


@pytest.fixture
def sample_risco(processamento_id: uuid.UUID, risco_id: uuid.UUID) -> Risco:
    """Fixture com uma entidade Risco de exemplo."""
    return Risco(
        id=risco_id,
        processamento_id=processamento_id,
        descricao="Single point of failure no API Gateway",
        severidade="alta",
        recomendacao_descricao="Implementar replicação e failover",
        recomendacao_prioridade="alta",
        componentes_afetados=["API Gateway"],
    )


@pytest.fixture
def sample_analise_result() -> AnaliseResultSchema:
    """Fixture com um resultado de análise válido."""
    return AnaliseResultSchema(
        componentes=[
            ComponenteSchema(
                nome="API Gateway",
                tipo=TipoComponente.API_GATEWAY,
                confianca=0.95,
                metadata=ComponenteMetadata(descricao="API Gateway da aplicação"),
            ),
            ComponenteSchema(
                nome="Database",
                tipo=TipoComponente.DATABASE,
                confianca=0.9,
                metadata=ComponenteMetadata(descricao="PostgreSQL database"),
            ),
        ],
        riscos=[
            RiscoSchema(
                descricao="Single point of failure",
                severidade=Severidade.ALTA,
                componentes_afetados=["API Gateway"],
                recomendacao=RecomendacaoSchema(
                    descricao="Implementar replicação",
                    prioridade=Severidade.ALTA,
                ),
            ),
        ],
    )


@pytest.fixture
def sample_llm_response() -> str:
    """Fixture com uma resposta JSON válida do LLM."""
    return """{
        "componentes": [
            {
                "nome": "API Gateway",
                "tipo": "api_gateway",
                "confianca": 0.95,
                "metadata": {"descricao": "API Gateway da aplicação"}
            },
            {
                "nome": "Database",
                "tipo": "database",
                "confianca": 0.9,
                "metadata": {"descricao": "PostgreSQL database"}
            }
        ],
        "riscos": [
            {
                "descricao": "Single point of failure",
                "severidade": "alta",
                "componentes_afetados": ["API Gateway"],
                "recomendacao": {
                    "descricao": "Implementar replicação",
                    "prioridade": "alta"
                }
            }
        ]
    }"""


@pytest.fixture
def sample_image_bytes() -> bytes:
    """Fixture com bytes de uma imagem de teste."""
    # Simple PNG header + minimal PNG data
    return b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    """Fixture com bytes de um PDF de teste."""
    # Minimal PDF structure
    return b"%PDF-1.4\n%EOF"


@pytest.fixture
async def async_client() -> AsyncClient:
    """Fixture para cliente HTTP assíncrono."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
