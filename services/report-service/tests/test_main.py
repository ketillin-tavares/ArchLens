"""Tests for the main application setup."""

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
        assert app.title == "report-service"

    def test_app_has_description(self) -> None:
        """Test that app has a description."""
        # Assert
        assert app.description is not None
        assert "relatórios" in app.description.lower()

    def test_app_has_version(self) -> None:
        """Test that app has a version."""
        # Assert
        assert app.version == "0.1.0"

    def test_app_routers_included(self) -> None:
        """Test that required routers are included."""
        # Arrange
        routes = [route.path for route in app.routes]

        # Assert
        assert "/v1/relatorios/{analise_id}" in routes
        assert "/health" in routes

    def test_app_exception_handlers_registered(self) -> None:
        """Test that exception handlers are registered."""
        # Arrange
        from src.domain.exceptions import RelatorioNaoEncontradoError

        # Assert
        assert RelatorioNaoEncontradoError in app.exception_handlers

    def test_app_openapi_schema(self) -> None:
        """Test that app can generate OpenAPI schema."""
        # Act
        schema = app.openapi()

        # Assert
        assert schema is not None
        assert "info" in schema
        assert schema["info"]["title"] == "report-service"
