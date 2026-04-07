"""Integration tests for health controller."""

from unittest.mock import AsyncMock, MagicMock, patch

from httpx import AsyncClient


class TestHealthController:
    """Integration tests for the health check endpoint."""

    async def test_health_check_success(self, async_client: AsyncClient) -> None:
        """Test GET /health returns 200 with healthy status."""
        # Arrange & Mock
        with patch("src.interface.controllers.health_controller.async_engine") as mock_engine:
            mock_connection = AsyncMock()
            mock_engine.connect.return_value.__aenter__.return_value = mock_connection

            with patch("src.interface.controllers.health_controller.aio_pika.connect_robust") as mock_pika:
                mock_conn = AsyncMock()
                mock_pika.return_value = mock_conn

                with patch("src.interface.controllers.health_controller.S3StorageClient") as mock_s3_cls:
                    mock_s3_instance = MagicMock()
                    mock_s3_instance.check_health = AsyncMock(return_value=True)
                    mock_s3_cls.return_value = mock_s3_instance

                    with patch("src.interface.controllers.health_controller.httpx.AsyncClient") as mock_http:
                        mock_http_instance = AsyncMock()
                        mock_response = MagicMock()
                        mock_response.status_code = 200
                        mock_http_instance.__aenter__.return_value = mock_http_instance
                        mock_http_instance.get = AsyncMock(return_value=mock_response)
                        mock_http.return_value = mock_http_instance

                        # Act
                        response = await async_client.get("/health")

                        # Assert
                        assert response.status_code == 200
                        data = response.json()
                        assert data["status"] == "healthy"
                        assert data["service"] == "report-service"
                        assert "dependencies" in data
                        assert "database" in data["dependencies"]
                        assert "rabbitmq" in data["dependencies"]

    async def test_health_check_database_ok(self, async_client: AsyncClient) -> None:
        """Test health check with database OK."""
        # Arrange & Mock
        with patch("src.interface.controllers.health_controller.async_engine") as mock_engine:
            mock_connection = AsyncMock()
            mock_engine.connect.return_value.__aenter__.return_value = mock_connection
            mock_connection.execute = AsyncMock()

            with patch("src.interface.controllers.health_controller.aio_pika.connect_robust") as mock_pika:
                mock_conn = AsyncMock()
                mock_pika.return_value = mock_conn

                with patch("src.interface.controllers.health_controller.S3StorageClient") as mock_s3_cls:
                    mock_s3_instance = MagicMock()
                    mock_s3_instance.check_health = AsyncMock(return_value=True)
                    mock_s3_cls.return_value = mock_s3_instance

                    with patch("src.interface.controllers.health_controller.httpx.AsyncClient") as mock_http:
                        mock_http_instance = AsyncMock()
                        mock_response = MagicMock()
                        mock_response.status_code = 200
                        mock_http_instance.__aenter__.return_value = mock_http_instance
                        mock_http_instance.get = AsyncMock(return_value=mock_response)
                        mock_http.return_value = mock_http_instance

                        # Act
                        response = await async_client.get("/health")

                        # Assert
                        assert response.status_code == 200
                        data = response.json()
                        assert data["dependencies"]["database"] == "ok"

    async def test_health_check_database_degraded(self, async_client: AsyncClient) -> None:
        """Test health check with database connection failure."""
        # Arrange & Mock
        with patch("src.interface.controllers.health_controller.async_engine") as mock_engine:
            mock_engine.connect.side_effect = Exception("DB connection failed")

            with patch("src.interface.controllers.health_controller.aio_pika.connect_robust") as mock_pika:
                mock_conn = AsyncMock()
                mock_pika.return_value = mock_conn

                with patch("src.interface.controllers.health_controller.S3StorageClient") as mock_s3_cls:
                    mock_s3_instance = MagicMock()
                    mock_s3_instance.check_health = AsyncMock(return_value=True)
                    mock_s3_cls.return_value = mock_s3_instance

                    with patch("src.interface.controllers.health_controller.httpx.AsyncClient") as mock_http:
                        mock_http_instance = AsyncMock()
                        mock_response = MagicMock()
                        mock_response.status_code = 200
                        mock_http_instance.__aenter__.return_value = mock_http_instance
                        mock_http_instance.get = AsyncMock(return_value=mock_response)
                        mock_http.return_value = mock_http_instance

                        # Act
                        response = await async_client.get("/health")

                        # Assert
                        assert response.status_code == 200
                        data = response.json()
                        assert data["dependencies"]["database"] == "degraded"

    async def test_health_check_rabbitmq_ok(self, async_client: AsyncClient) -> None:
        """Test health check with RabbitMQ OK."""
        # Arrange & Mock
        with patch("src.interface.controllers.health_controller.async_engine") as mock_engine:
            mock_connection = AsyncMock()
            mock_engine.connect.return_value.__aenter__.return_value = mock_connection

            with patch("src.interface.controllers.health_controller.aio_pika.connect_robust") as mock_pika:
                mock_conn = AsyncMock()
                mock_pika.return_value = mock_conn

                with patch("src.interface.controllers.health_controller.S3StorageClient") as mock_s3_cls:
                    mock_s3_instance = MagicMock()
                    mock_s3_instance.check_health = AsyncMock(return_value=True)
                    mock_s3_cls.return_value = mock_s3_instance

                    with patch("src.interface.controllers.health_controller.httpx.AsyncClient") as mock_http:
                        mock_http_instance = AsyncMock()
                        mock_response = MagicMock()
                        mock_response.status_code = 200
                        mock_http_instance.__aenter__.return_value = mock_http_instance
                        mock_http_instance.get = AsyncMock(return_value=mock_response)
                        mock_http.return_value = mock_http_instance

                        # Act
                        response = await async_client.get("/health")

                        # Assert
                        assert response.status_code == 200
                        data = response.json()
                        assert data["dependencies"]["rabbitmq"] == "ok"

    async def test_health_check_rabbitmq_degraded(self, async_client: AsyncClient) -> None:
        """Test health check with RabbitMQ connection failure."""
        # Arrange & Mock
        with patch("src.interface.controllers.health_controller.async_engine") as mock_engine:
            mock_connection = AsyncMock()
            mock_engine.connect.return_value.__aenter__.return_value = mock_connection

            with patch("src.interface.controllers.health_controller.aio_pika.connect_robust") as mock_pika:
                mock_pika.side_effect = Exception("RabbitMQ connection failed")

                with patch("src.interface.controllers.health_controller.S3StorageClient") as mock_s3_cls:
                    mock_s3_instance = MagicMock()
                    mock_s3_instance.check_health = AsyncMock(return_value=True)
                    mock_s3_cls.return_value = mock_s3_instance

                    with patch("src.interface.controllers.health_controller.httpx.AsyncClient") as mock_http:
                        mock_http_instance = AsyncMock()
                        mock_response = MagicMock()
                        mock_response.status_code = 200
                        mock_http_instance.__aenter__.return_value = mock_http_instance
                        mock_http_instance.get = AsyncMock(return_value=mock_response)
                        mock_http.return_value = mock_http_instance

                        # Act
                        response = await async_client.get("/health")

                        # Assert
                        assert response.status_code == 200
                        data = response.json()
                        assert data["dependencies"]["rabbitmq"] == "degraded"

    async def test_health_check_s3_degraded(self, async_client: AsyncClient) -> None:
        """Test health check with S3 connection failure."""
        # Arrange & Mock
        with patch("src.interface.controllers.health_controller.async_engine") as mock_engine:
            mock_connection = AsyncMock()
            mock_engine.connect.return_value.__aenter__.return_value = mock_connection

            with patch("src.interface.controllers.health_controller.aio_pika.connect_robust") as mock_pika:
                mock_conn = AsyncMock()
                mock_pika.return_value = mock_conn

                with patch("src.interface.controllers.health_controller.S3StorageClient") as mock_s3_cls:
                    mock_s3_instance = MagicMock()
                    mock_s3_instance.check_health = AsyncMock(return_value=False)
                    mock_s3_cls.return_value = mock_s3_instance

                    with patch("src.interface.controllers.health_controller.httpx.AsyncClient") as mock_http:
                        mock_http_instance = AsyncMock()
                        mock_response = MagicMock()
                        mock_response.status_code = 200
                        mock_http_instance.__aenter__.return_value = mock_http_instance
                        mock_http_instance.get = AsyncMock(return_value=mock_response)
                        mock_http.return_value = mock_http_instance

                        # Act
                        response = await async_client.get("/health")

                        # Assert
                        assert response.status_code == 200
                        data = response.json()
                        assert data["dependencies"]["s3"] == "degraded"

    async def test_health_check_llm_api_degraded(self, async_client: AsyncClient) -> None:
        """Test health check with LLM API connection failure."""
        # Arrange & Mock
        with patch("src.interface.controllers.health_controller.async_engine") as mock_engine:
            mock_connection = AsyncMock()
            mock_engine.connect.return_value.__aenter__.return_value = mock_connection

            with patch("src.interface.controllers.health_controller.aio_pika.connect_robust") as mock_pika:
                mock_conn = AsyncMock()
                mock_pika.return_value = mock_conn

                with patch("src.interface.controllers.health_controller.S3StorageClient") as mock_s3_cls:
                    mock_s3_instance = MagicMock()
                    mock_s3_instance.check_health = AsyncMock(return_value=True)
                    mock_s3_cls.return_value = mock_s3_instance

                    with patch("src.interface.controllers.health_controller.httpx.AsyncClient") as mock_http:
                        mock_http_instance = AsyncMock()
                        mock_response = MagicMock()
                        mock_response.status_code = 500
                        mock_http_instance.__aenter__.return_value = mock_http_instance
                        mock_http_instance.get = AsyncMock(return_value=mock_response)
                        mock_http.return_value = mock_http_instance

                        # Act
                        response = await async_client.get("/health")

                        # Assert
                        assert response.status_code == 200
                        data = response.json()
                        assert data["dependencies"]["llm_api"] == "degraded"

    async def test_health_check_both_degraded(self, async_client: AsyncClient) -> None:
        """Test health check with both DB and RabbitMQ degraded."""
        # Arrange & Mock
        with patch("src.interface.controllers.health_controller.async_engine") as mock_engine:
            mock_engine.connect.side_effect = Exception("DB error")

            with patch("src.interface.controllers.health_controller.aio_pika.connect_robust") as mock_pika:
                mock_pika.side_effect = Exception("RabbitMQ error")

                with patch("src.interface.controllers.health_controller.S3StorageClient") as mock_s3_cls:
                    mock_s3_instance = MagicMock()
                    mock_s3_instance.check_health = AsyncMock(return_value=True)
                    mock_s3_cls.return_value = mock_s3_instance

                    with patch("src.interface.controllers.health_controller.httpx.AsyncClient") as mock_http:
                        mock_http_instance = AsyncMock()
                        mock_response = MagicMock()
                        mock_response.status_code = 200
                        mock_http_instance.__aenter__.return_value = mock_http_instance
                        mock_http_instance.get = AsyncMock(return_value=mock_response)
                        mock_http.return_value = mock_http_instance

                        # Act
                        response = await async_client.get("/health")

                        # Assert
                        assert response.status_code == 200
                        data = response.json()
                        assert data["status"] == "healthy"
                        assert data["dependencies"]["database"] == "degraded"
                        assert data["dependencies"]["rabbitmq"] == "degraded"

    async def test_health_check_response_format(self, async_client: AsyncClient) -> None:
        """Test health check response has correct structure."""
        # Arrange & Mock
        with patch("src.interface.controllers.health_controller.async_engine") as mock_engine:
            mock_connection = AsyncMock()
            mock_engine.connect.return_value.__aenter__.return_value = mock_connection

            with patch("src.interface.controllers.health_controller.aio_pika.connect_robust") as mock_pika:
                mock_conn = AsyncMock()
                mock_pika.return_value = mock_conn

                with patch("src.interface.controllers.health_controller.S3StorageClient") as mock_s3_cls:
                    mock_s3_instance = MagicMock()
                    mock_s3_instance.check_health = AsyncMock(return_value=True)
                    mock_s3_cls.return_value = mock_s3_instance

                    with patch("src.interface.controllers.health_controller.httpx.AsyncClient") as mock_http:
                        mock_http_instance = AsyncMock()
                        mock_response = MagicMock()
                        mock_response.status_code = 200
                        mock_http_instance.__aenter__.return_value = mock_http_instance
                        mock_http_instance.get = AsyncMock(return_value=mock_response)
                        mock_http.return_value = mock_http_instance

                        # Act
                        response = await async_client.get("/health")

                        # Assert
                        assert response.status_code == 200
                        data = response.json()
                        assert set(data.keys()) == {"status", "service", "dependencies"}
                        assert isinstance(data["status"], str)
                        assert isinstance(data["service"], str)
                        assert isinstance(data["dependencies"], dict)
