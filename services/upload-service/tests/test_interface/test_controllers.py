"""Tests for FastAPI controllers."""

import uuid
from datetime import UTC, datetime
from io import BytesIO
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.domain.entities import Analise
from src.domain.exceptions import (
    AnaliseNaoEncontradaError,
    ArquivoInvalidoError,
    ArquivoTamanhoExcedidoError,
)
from src.domain.value_objects import StatusAnalise
from src.interface.controllers.v1.analise_controller import router as analise_router


@pytest.fixture
def app() -> FastAPI:
    """Create a test FastAPI app with the analise router."""
    app = FastAPI()
    app.include_router(analise_router, prefix="/api/v1")

    # Add exception handlers
    @app.exception_handler(ArquivoInvalidoError)
    async def arquivo_invalido_handler(request, exc):
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(ArquivoTamanhoExcedidoError)
    async def arquivo_tamanho_handler(request, exc):
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=413, content={"detail": str(exc)})

    @app.exception_handler(AnaliseNaoEncontradaError)
    async def analise_nao_encontrada_handler(request, exc):
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=404, content={"detail": str(exc)})

    return app


@pytest.fixture
async def async_client(app: FastAPI) -> AsyncClient:
    """Create an async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


class TestSubmitDiagramController:
    """Tests for POST /api/v1/analises endpoint."""

    @pytest.mark.asyncio
    async def test_submit_diagram_400_invalid_file_type(self, async_client: AsyncClient) -> None:
        """Test invalid file type returns 400 Bad Request."""
        # Arrange
        file_content = b"fake_doc_data"
        file = BytesIO(file_content)

        with (
            patch("src.interface.controllers.v1.analise_controller.get_session") as mock_get_session,
            patch("src.interface.controllers.v1.analise_controller.SQLAlchemyDiagramaRepository") as mock_diagrama_repo,
            patch("src.interface.controllers.v1.analise_controller.SQLAlchemyAnaliseRepository") as mock_analise_repo,
            patch("src.interface.controllers.v1.analise_controller.S3FileStorageGateway") as mock_file_storage,
            patch("src.interface.controllers.v1.analise_controller._get_publisher_gateway") as mock_publisher_gateway,
        ):
            # Setup mocks
            mock_session = AsyncMock()
            mock_get_session.return_value = mock_session

            mock_diagrama_repo_instance = AsyncMock()
            mock_diagrama_repo.return_value = mock_diagrama_repo_instance

            mock_analise_repo_instance = AsyncMock()
            mock_analise_repo.return_value = mock_analise_repo_instance

            mock_file_storage_instance = AsyncMock()
            mock_file_storage.return_value = mock_file_storage_instance

            mock_publisher_instance = AsyncMock()
            mock_publisher_gateway.return_value = mock_publisher_instance

            # Act
            content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            response = await async_client.post(
                "/api/v1/analises",
                files={"file": ("documento.docx", file, content_type)},
            )

            # Assert
            assert response.status_code == 400
            data = response.json()
            assert "detail" in data

    @pytest.mark.asyncio
    async def test_submit_diagram_413_file_too_large(self, async_client: AsyncClient) -> None:
        """Test oversized file returns 413 Payload Too Large."""
        # Arrange
        tamanho_excedido = 11 * 1024 * 1024  # 11MB
        file_content = b"x" * tamanho_excedido
        file = BytesIO(file_content)

        with (
            patch("src.interface.controllers.v1.analise_controller.get_session") as mock_get_session,
            patch("src.interface.controllers.v1.analise_controller.SQLAlchemyDiagramaRepository") as mock_diagrama_repo,
            patch("src.interface.controllers.v1.analise_controller.SQLAlchemyAnaliseRepository") as mock_analise_repo,
            patch("src.interface.controllers.v1.analise_controller.S3FileStorageGateway") as mock_file_storage,
            patch("src.interface.controllers.v1.analise_controller._get_publisher_gateway") as mock_publisher_gateway,
        ):
            # Setup mocks
            mock_session = AsyncMock()
            mock_get_session.return_value = mock_session

            mock_diagrama_repo_instance = AsyncMock()
            mock_diagrama_repo.return_value = mock_diagrama_repo_instance

            mock_analise_repo_instance = AsyncMock()
            mock_analise_repo.return_value = mock_analise_repo_instance

            mock_file_storage_instance = AsyncMock()
            mock_file_storage.return_value = mock_file_storage_instance

            mock_publisher_instance = AsyncMock()
            mock_publisher_gateway.return_value = mock_publisher_instance

            # Act
            response = await async_client.post(
                "/api/v1/analises",
                files={"file": ("grande.png", file, "image/png")},
            )

            # Assert
            assert response.status_code == 413
            data = response.json()
            assert "detail" in data


class TestGetAnalysisStatusController:
    """Tests for GET /api/v1/analises/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_analysis_status_200_success(self, async_client: AsyncClient) -> None:
        """Test successful status retrieval returns 200 OK."""
        # Arrange
        analise_id = uuid.uuid4()
        diagrama_id = uuid.uuid4()
        criado_em = datetime.now(UTC)
        atualizado_em = datetime.now(UTC)

        with (
            patch("src.interface.controllers.v1.analise_controller.get_session") as mock_get_session,
            patch("src.interface.controllers.v1.analise_controller.SQLAlchemyAnaliseRepository") as mock_analise_repo,
        ):
            # Setup mocks
            mock_session = AsyncMock()
            mock_get_session.return_value = mock_session

            mock_analise_repo_instance = AsyncMock()
            mock_analise_repo.return_value = mock_analise_repo_instance

            mock_analise_repo_instance.buscar_por_id.return_value = Analise(
                id=analise_id,
                diagrama_id=diagrama_id,
                status=StatusAnalise.EM_PROCESSAMENTO,
                criado_em=criado_em,
                atualizado_em=atualizado_em,
            )

            # Act
            response = await async_client.get(f"/api/v1/analises/{analise_id}")

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == str(analise_id)
            assert data["diagrama_id"] == str(diagrama_id)
            assert data["status"] == StatusAnalise.EM_PROCESSAMENTO.value

    @pytest.mark.asyncio
    async def test_get_analysis_status_404_not_found(self, async_client: AsyncClient) -> None:
        """Test non-existent analysis returns 404 Not Found."""
        # Arrange
        analise_id = uuid.uuid4()

        with (
            patch("src.interface.controllers.v1.analise_controller.get_session") as mock_get_session,
            patch("src.interface.controllers.v1.analise_controller.SQLAlchemyAnaliseRepository") as mock_analise_repo,
        ):
            # Setup mocks
            mock_session = AsyncMock()
            mock_get_session.return_value = mock_session

            mock_analise_repo_instance = AsyncMock()
            mock_analise_repo.return_value = mock_analise_repo_instance
            mock_analise_repo_instance.buscar_por_id.return_value = None

            # Act
            response = await async_client.get(f"/api/v1/analises/{analise_id}")

            # Assert
            assert response.status_code == 404
            data = response.json()
            assert "detail" in data

    @pytest.mark.asyncio
    async def test_get_analysis_status_recebido(self, async_client: AsyncClient) -> None:
        """Test retrieval of newly received analysis."""
        # Arrange
        analise_id = uuid.uuid4()
        diagrama_id = uuid.uuid4()

        with (
            patch("src.interface.controllers.v1.analise_controller.get_session") as mock_get_session,
            patch("src.interface.controllers.v1.analise_controller.SQLAlchemyAnaliseRepository") as mock_analise_repo,
        ):
            # Setup mocks
            mock_session = AsyncMock()
            mock_get_session.return_value = mock_session

            mock_analise_repo_instance = AsyncMock()
            mock_analise_repo.return_value = mock_analise_repo_instance

            mock_analise_repo_instance.buscar_por_id.return_value = Analise(
                id=analise_id,
                diagrama_id=diagrama_id,
                status=StatusAnalise.RECEBIDO,
            )

            # Act
            response = await async_client.get(f"/api/v1/analises/{analise_id}")

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == StatusAnalise.RECEBIDO.value

    @pytest.mark.asyncio
    async def test_get_analysis_status_analisado(self, async_client: AsyncClient) -> None:
        """Test retrieval of completed analysis."""
        # Arrange
        analise_id = uuid.uuid4()
        diagrama_id = uuid.uuid4()

        with (
            patch("src.interface.controllers.v1.analise_controller.get_session") as mock_get_session,
            patch("src.interface.controllers.v1.analise_controller.SQLAlchemyAnaliseRepository") as mock_analise_repo,
        ):
            # Setup mocks
            mock_session = AsyncMock()
            mock_get_session.return_value = mock_session

            mock_analise_repo_instance = AsyncMock()
            mock_analise_repo.return_value = mock_analise_repo_instance

            mock_analise_repo_instance.buscar_por_id.return_value = Analise(
                id=analise_id,
                diagrama_id=diagrama_id,
                status=StatusAnalise.ANALISADO,
            )

            # Act
            response = await async_client.get(f"/api/v1/analises/{analise_id}")

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == StatusAnalise.ANALISADO.value

    @pytest.mark.asyncio
    async def test_get_analysis_status_with_error(self, async_client: AsyncClient) -> None:
        """Test retrieval of analysis with error details."""
        # Arrange
        analise_id = uuid.uuid4()
        diagrama_id = uuid.uuid4()
        erro_detalhe = "Estrutura de diagrama inválida"

        with (
            patch("src.interface.controllers.v1.analise_controller.get_session") as mock_get_session,
            patch("src.interface.controllers.v1.analise_controller.SQLAlchemyAnaliseRepository") as mock_analise_repo,
        ):
            # Setup mocks
            mock_session = AsyncMock()
            mock_get_session.return_value = mock_session

            mock_analise_repo_instance = AsyncMock()
            mock_analise_repo.return_value = mock_analise_repo_instance

            mock_analise_repo_instance.buscar_por_id.return_value = Analise(
                id=analise_id,
                diagrama_id=diagrama_id,
                status=StatusAnalise.ERRO,
                erro_detalhe=erro_detalhe,
            )

            # Act
            response = await async_client.get(f"/api/v1/analises/{analise_id}")

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == StatusAnalise.ERRO.value
            assert data["erro_detalhe"] == erro_detalhe
