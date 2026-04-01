"""Tests for health check controller."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.interface.controllers.health_controller import (
    _check_database,
    _check_rabbitmq,
    _check_s3,
)
from src.interface.controllers.health_controller import (
    router as health_router,
)


@pytest.fixture
def app() -> FastAPI:
    """Create a test FastAPI app with the health router."""
    app = FastAPI()
    app.include_router(health_router)
    return app


@pytest.fixture
async def async_client(app: FastAPI) -> AsyncClient:
    """Create an async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


class TestHealthCheckEndpoint:
    """Tests for GET /health endpoint."""

    @pytest.mark.asyncio
    async def test_health_check_all_ok(self, async_client: AsyncClient) -> None:
        """Test health check when all dependencies are healthy."""
        # Arrange
        with (
            patch("src.interface.controllers.health_controller._check_database") as mock_db,
            patch("src.interface.controllers.health_controller._check_rabbitmq") as mock_rabbit,
            patch("src.interface.controllers.health_controller._check_s3") as mock_s3,
        ):
            mock_db.return_value = "ok"
            mock_rabbit.return_value = "ok"
            mock_s3.return_value = "ok"

            # Act
            response = await async_client.get("/health")

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "upload-service"
            assert data["dependencies"]["database"] == "ok"
            assert data["dependencies"]["rabbitmq"] == "ok"
            assert data["dependencies"]["s3"] == "ok"

    @pytest.mark.asyncio
    async def test_health_check_database_degraded(self, async_client: AsyncClient) -> None:
        """Test health check when database is degraded."""
        # Arrange
        with (
            patch("src.interface.controllers.health_controller._check_database") as mock_db,
            patch("src.interface.controllers.health_controller._check_rabbitmq") as mock_rabbit,
            patch("src.interface.controllers.health_controller._check_s3") as mock_s3,
        ):
            mock_db.return_value = "degraded"
            mock_rabbit.return_value = "ok"
            mock_s3.return_value = "ok"

            # Act
            response = await async_client.get("/health")

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["dependencies"]["database"] == "degraded"

    @pytest.mark.asyncio
    async def test_health_check_rabbitmq_degraded(self, async_client: AsyncClient) -> None:
        """Test health check when RabbitMQ is degraded."""
        # Arrange
        with (
            patch("src.interface.controllers.health_controller._check_database") as mock_db,
            patch("src.interface.controllers.health_controller._check_rabbitmq") as mock_rabbit,
            patch("src.interface.controllers.health_controller._check_s3") as mock_s3,
        ):
            mock_db.return_value = "ok"
            mock_rabbit.return_value = "degraded"
            mock_s3.return_value = "ok"

            # Act
            response = await async_client.get("/health")

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["dependencies"]["rabbitmq"] == "degraded"

    @pytest.mark.asyncio
    async def test_health_check_s3_degraded(self, async_client: AsyncClient) -> None:
        """Test health check when S3 is degraded."""
        # Arrange
        with (
            patch("src.interface.controllers.health_controller._check_database") as mock_db,
            patch("src.interface.controllers.health_controller._check_rabbitmq") as mock_rabbit,
            patch("src.interface.controllers.health_controller._check_s3") as mock_s3,
        ):
            mock_db.return_value = "ok"
            mock_rabbit.return_value = "ok"
            mock_s3.return_value = "degraded"

            # Act
            response = await async_client.get("/health")

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["dependencies"]["s3"] == "degraded"


class TestCheckDatabase:
    """Tests for _check_database function."""

    @pytest.mark.asyncio
    async def test_check_database_success(self) -> None:
        """Test successful database check."""
        # Arrange
        from unittest.mock import AsyncMock

        mock_conn = AsyncMock()
        mock_engine = MagicMock()

        # Setup async context manager properly
        async_context_manager = MagicMock()
        async_context_manager.__aenter__ = AsyncMock(return_value=mock_conn)
        async_context_manager.__aexit__ = AsyncMock(return_value=None)
        mock_engine.connect.return_value = async_context_manager

        with patch("src.interface.controllers.health_controller.async_engine", mock_engine):
            # Act
            result = await _check_database()

            # Assert
            assert result == "ok"
            mock_conn.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_database_failure(self) -> None:
        """Test database check when connection fails."""
        # Arrange
        mock_engine = AsyncMock()
        mock_engine.connect.side_effect = Exception("Connection refused")

        with patch("src.interface.controllers.health_controller.async_engine", mock_engine):
            # Act
            result = await _check_database()

            # Assert
            assert result == "degraded"


class TestCheckRabbitMQ:
    """Tests for _check_rabbitmq function."""

    @pytest.mark.asyncio
    async def test_check_rabbitmq_success(self) -> None:
        """Test successful RabbitMQ check."""
        # Arrange
        mock_connection = AsyncMock()

        with patch("src.interface.controllers.health_controller.aio_pika.connect_robust") as mock_connect:
            mock_connect.return_value = mock_connection

            # Act
            result = await _check_rabbitmq()

            # Assert
            assert result == "ok"
            mock_connection.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_rabbitmq_failure(self) -> None:
        """Test RabbitMQ check when connection fails."""
        # Arrange
        with patch("src.interface.controllers.health_controller.aio_pika.connect_robust") as mock_connect:
            mock_connect.side_effect = Exception("Connection timeout")

            # Act
            result = await _check_rabbitmq()

            # Assert
            assert result == "degraded"

    @pytest.mark.asyncio
    async def test_check_rabbitmq_timeout(self) -> None:
        """Test RabbitMQ check with timeout."""
        # Arrange
        with patch("src.interface.controllers.health_controller.aio_pika.connect_robust") as mock_connect:
            mock_connect.side_effect = TimeoutError("Connection timeout")

            # Act
            result = await _check_rabbitmq()

            # Assert
            assert result == "degraded"


class TestCheckS3:
    """Tests for _check_s3 function."""

    @pytest.mark.asyncio
    async def test_check_s3_success(self) -> None:
        """Test successful S3 health check."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.check_health.return_value = True

        with patch("src.interface.controllers.health_controller.S3StorageClient") as mock_s3_class:
            mock_s3_class.return_value = mock_client

            # Act
            result = await _check_s3()

            # Assert
            assert result == "ok"
            mock_client.check_health.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_s3_unhealthy(self) -> None:
        """Test S3 health check when service reports unhealthy."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.check_health.return_value = False

        with patch("src.interface.controllers.health_controller.S3StorageClient") as mock_s3_class:
            mock_s3_class.return_value = mock_client

            # Act
            result = await _check_s3()

            # Assert
            assert result == "degraded"

    @pytest.mark.asyncio
    async def test_check_s3_exception(self) -> None:
        """Test S3 health check when exception is raised."""
        # Arrange
        with patch("src.interface.controllers.health_controller.S3StorageClient") as mock_s3_class:
            mock_s3_class.side_effect = Exception("S3 service error")

            # Act
            result = await _check_s3()

            # Assert
            assert result == "degraded"
