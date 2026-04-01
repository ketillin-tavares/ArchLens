"""Tests for main application setup."""

from unittest.mock import AsyncMock, patch

import pytest

from src.domain.exceptions import (
    AnaliseNaoEncontradaError,
    ArquivoInvalidoError,
    ArquivoTamanhoExcedidoError,
)
from src.main import (
    _status_update_handler,
    app,
)


class TestStatusUpdateHandler:
    """Tests for _status_update_handler function."""

    @pytest.mark.asyncio
    async def test_status_update_handler_success(self) -> None:
        """Test successful status update handling."""
        # Arrange
        analise_id = "test-uuid-123"
        novo_status = "em_processamento"

        with (
            patch("src.main.async_session_factory") as mock_session_factory,
            patch("src.main.SQLAlchemyAnaliseRepository") as mock_repo_class,
            patch("src.main.HandleStatusUpdate") as mock_use_case_class,
            patch("src.main.MetricsRecorder") as mock_metrics,
        ):
            # Setup mocks
            mock_session = AsyncMock()
            mock_session_factory.return_value.__aenter__.return_value = mock_session

            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo

            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case

            # Act
            await _status_update_handler(analise_id, novo_status)

            # Assert
            mock_use_case.execute.assert_called_once_with(analise_id, novo_status, None)
            mock_session.commit.assert_called_once()
            mock_metrics.record_analise_por_status.assert_called_once_with(novo_status)

    @pytest.mark.asyncio
    async def test_status_update_handler_with_error_detail(self) -> None:
        """Test status update handling with error details."""
        # Arrange
        analise_id = "test-uuid-123"
        novo_status = "erro"
        erro_detalhe = "Falha ao processar diagrama"

        with (
            patch("src.main.async_session_factory") as mock_session_factory,
            patch("src.main.SQLAlchemyAnaliseRepository") as mock_repo_class,
            patch("src.main.HandleStatusUpdate") as mock_use_case_class,
            patch("src.main.MetricsRecorder") as mock_metrics,
        ):
            # Setup mocks
            mock_session = AsyncMock()
            mock_session_factory.return_value.__aenter__.return_value = mock_session

            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo

            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case

            # Act
            await _status_update_handler(analise_id, novo_status, erro_detalhe)

            # Assert
            mock_use_case.execute.assert_called_once_with(analise_id, novo_status, erro_detalhe)
            mock_metrics.record_analise_por_status.assert_called_once_with(novo_status)
            mock_metrics.record_falha.assert_called_once()

    @pytest.mark.asyncio
    async def test_status_update_handler_non_error_status(self) -> None:
        """Test status update handling with non-error status does not record failure."""
        # Arrange
        analise_id = "test-uuid-123"
        novo_status = "analisado"

        with (
            patch("src.main.async_session_factory") as mock_session_factory,
            patch("src.main.SQLAlchemyAnaliseRepository") as mock_repo_class,
            patch("src.main.HandleStatusUpdate") as mock_use_case_class,
            patch("src.main.MetricsRecorder") as mock_metrics,
        ):
            # Setup mocks
            mock_session = AsyncMock()
            mock_session_factory.return_value.__aenter__.return_value = mock_session

            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo

            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case

            # Act
            await _status_update_handler(analise_id, novo_status)

            # Assert
            mock_metrics.record_analise_por_status.assert_called_once()
            mock_metrics.record_falha.assert_not_called()


class TestAppSetup:
    """Tests for FastAPI application setup."""

    def test_app_creation(self) -> None:
        """Test that the FastAPI app is created."""
        # Assert
        assert app is not None
        assert app.title == "upload-service"
        assert app.version == "0.1.0"

    def test_app_has_routers(self) -> None:
        """Test that the app includes routers."""
        # Assert
        assert len(app.routes) > 0

    def test_app_has_exception_handlers(self) -> None:
        """Test that exception handlers are registered."""
        # Assert - Check if exception handlers are set up
        exception_handlers = app.exception_handlers
        assert len(exception_handlers) > 0


class TestExceptionHandlers:
    """Tests for exception handlers."""

    @pytest.mark.asyncio
    async def test_arquivo_invalido_exception_handler(self) -> None:
        """Test ArquivoInvalidoError exception handler."""
        # Arrange - just verify the handler is registered
        # We can't directly call the handler, but we can verify it's registered
        assert ArquivoInvalidoError in app.exception_handlers

    @pytest.mark.asyncio
    async def test_arquivo_tamanho_exception_handler(self) -> None:
        """Test ArquivoTamanhoExcedidoError exception handler."""
        # Arrange - just verify the handler is registered
        assert ArquivoTamanhoExcedidoError in app.exception_handlers

    @pytest.mark.asyncio
    async def test_analise_nao_encontrada_exception_handler(self) -> None:
        """Test AnaliseNaoEncontradaError exception handler."""
        # Arrange - just verify the handler is registered
        assert AnaliseNaoEncontradaError in app.exception_handlers


class TestLifespanContext:
    """Tests for lifespan context manager."""

    def test_app_has_routes(self) -> None:
        """Test that application has routes registered."""
        # The app should have routes from the routers
        assert len(app.routes) > 0
