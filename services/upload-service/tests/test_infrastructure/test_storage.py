"""Tests for S3 storage client."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.infrastructure.storage.s3_client import S3StorageClient, storage_circuit_breaker


class TestS3StorageClient:
    """Tests for S3StorageClient."""

    def test_client_initialization(self) -> None:
        """Test S3StorageClient initialization."""
        # Act
        client = S3StorageClient()

        # Assert
        assert client is not None
        assert client._session is not None

    def test_get_client_kwargs(self) -> None:
        """Test _get_client_kwargs returns proper configuration."""
        # Arrange
        client = S3StorageClient()

        # Act
        kwargs = client._get_client_kwargs()

        # Assert
        assert "service_name" in kwargs
        assert kwargs["service_name"] == "s3"
        assert "endpoint_url" in kwargs
        assert "aws_access_key_id" in kwargs
        assert "aws_secret_access_key" in kwargs
        assert "region_name" in kwargs

    @pytest.mark.asyncio
    async def test_upload_file_success(self) -> None:
        """Test successful file upload to S3."""
        # Arrange
        client = S3StorageClient()
        file_bytes = b"test file content"
        storage_path = "diagramas/test-uuid.png"
        content_type = "image/png"

        mock_s3 = AsyncMock()
        mock_session = MagicMock()
        mock_session.client.return_value.__aenter__ = AsyncMock(return_value=mock_s3)
        mock_session.client.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch.object(client, "_session", mock_session):
            # Act
            result = await client.upload_file(file_bytes, storage_path, content_type)

            # Assert
            assert result == storage_path
            mock_s3.put_object.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_health_success(self) -> None:
        """Test health check when S3 is accessible."""
        # Arrange
        client = S3StorageClient()

        mock_s3 = AsyncMock()
        mock_session = MagicMock()
        mock_session.client.return_value.__aenter__ = AsyncMock(return_value=mock_s3)
        mock_session.client.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch.object(client, "_session", mock_session):
            # Act
            result = await client.check_health()

            # Assert
            assert result is True
            mock_s3.head_bucket.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_health_failure(self) -> None:
        """Test health check when S3 is not accessible."""
        # Arrange
        client = S3StorageClient()

        mock_session = MagicMock()
        mock_session.client.side_effect = Exception("Connection refused")

        with patch.object(client, "_session", mock_session):
            # Act
            result = await client.check_health()

            # Assert
            assert result is False

    @pytest.mark.asyncio
    async def test_download_file(self) -> None:
        """Test downloading a file from S3."""
        # Arrange
        client = S3StorageClient()
        storage_path = "diagramas/test-uuid.png"
        expected_content = b"file content from s3"

        mock_body = AsyncMock()
        mock_body.read = AsyncMock(return_value=expected_content)
        mock_response = {"Body": mock_body}

        mock_s3 = AsyncMock()
        mock_s3.get_object = AsyncMock(return_value=mock_response)

        mock_session = MagicMock()
        mock_session.client.return_value.__aenter__ = AsyncMock(return_value=mock_s3)
        mock_session.client.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch.object(client, "_session", mock_session):
            # Act
            result = await client.download_file(storage_path)

            # Assert
            assert result == expected_content
            mock_s3.get_object.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_presigned_url(self) -> None:
        """Test generating a presigned URL for S3 object."""
        # Arrange
        client = S3StorageClient()
        s3_key = "reports/test-uuid.md"
        expected_url = "https://s3.example.com/reports/test-uuid.md?signed=abc"

        mock_s3 = AsyncMock()
        mock_s3.generate_presigned_url = AsyncMock(return_value=expected_url)

        mock_session = MagicMock()
        mock_session.client.return_value.__aenter__ = AsyncMock(return_value=mock_s3)
        mock_session.client.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch.object(client, "_session", mock_session):
            # Act
            result = await client.generate_presigned_url(s3_key, 3600)

            # Assert
            assert result == expected_url
            mock_s3.generate_presigned_url.assert_called_once_with(
                "get_object",
                Params={"Bucket": client._settings.bucket_name, "Key": s3_key},
                ExpiresIn=3600,
            )


class TestStorageCircuitBreaker:
    """Tests for storage circuit breaker configuration."""

    def test_circuit_breaker_configuration(self) -> None:
        """Test circuit breaker is properly configured."""
        # Assert
        assert storage_circuit_breaker is not None
        assert storage_circuit_breaker.fail_max == 3
        assert storage_circuit_breaker.reset_timeout == 30
