"""Tests for the main application setup and lifespan."""

import asyncio
from unittest.mock import MagicMock

from fastapi import FastAPI

from src.main import app


class TestAppSetup:
    """Tests for the FastAPI application setup."""

    def test_app_is_fastapi_instance(self) -> None:
        """Test that app is a FastAPI instance."""
        # Assert
        assert isinstance(app, FastAPI)

    def test_app_has_title(self) -> None:
        """Test that app has a title."""
        # Assert
        assert app.title == "processing-service"

    def test_app_has_description(self) -> None:
        """Test that app has a description."""
        # Assert
        assert app.description is not None
        assert "processamento" in app.description.lower() or "diagrama" in app.description.lower()

    def test_app_has_version(self) -> None:
        """Test that app has a version."""
        # Assert
        assert app.version == "0.1.0"

    def test_app_routers_included(self) -> None:
        """Test that required routers are included."""
        # Arrange
        routes = [route.path for route in app.routes]

        # Assert
        assert "/v1/processamentos/{analise_id}" in routes
        assert "/health" in routes

    def test_app_exception_handlers_registered(self) -> None:
        """Test that exception handlers are registered."""
        # Arrange
        from src.domain.exceptions import ProcessamentoNaoEncontradoError

        # Assert
        assert ProcessamentoNaoEncontradoError in app.exception_handlers

    def test_app_openapi_schema(self) -> None:
        """Test that app can generate OpenAPI schema."""
        # Act
        schema = app.openapi()

        # Assert
        assert schema is not None
        assert "info" in schema
        assert schema["info"]["title"] == "processing-service"


class TestDiagramHandler:
    """Tests for the _diagram_handler function."""

    def test_diagram_handler_exists(self) -> None:
        """Test that _diagram_handler is defined and callable."""
        # Arrange
        from src.main import _diagram_handler

        # Act & Assert
        assert callable(_diagram_handler)


class TestLifespan:
    """Tests for the lifespan context manager."""

    def test_lifespan_generator(self) -> None:
        """Test lifespan is an async context manager."""
        # Arrange
        from src.main import lifespan

        # Act
        # Just verify it's callable and returns an async context manager
        generator = lifespan(app)

        # Assert
        assert generator is not None


class TestProcessamentoNotFoundHandler:
    """Tests for ProcessamentoNaoEncontradoError exception handler."""

    def test_exception_handler_returns_404(self) -> None:
        """Test exception handler returns 404 response."""
        # Arrange
        from fastapi import Request

        from src.domain.exceptions import ProcessamentoNaoEncontradoError
        from src.main import app as fastapi_app

        exc = ProcessamentoNaoEncontradoError("Processamento não encontrado")
        mock_request = MagicMock(spec=Request)

        handler = fastapi_app.exception_handlers[ProcessamentoNaoEncontradoError]

        # Act
        response = asyncio.run(handler(mock_request, exc))

        # Assert
        assert response.status_code == 404
        assert "detail" in response.body.decode()
