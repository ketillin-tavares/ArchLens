"""Unit tests for infrastructure storage clients."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.infrastructure.storage.s3_client import S3StorageClient


class TestS3StorageClient:
    """Tests for the S3StorageClient class."""

    def test_initialization(self) -> None:
        """Test that S3StorageClient initializes correctly."""
        # Act
        client = S3StorageClient()

        # Assert
        assert client._session is not None
        assert client._settings is not None

    def test_get_client_kwargs(self) -> None:
        """Test that _get_client_kwargs returns correct configuration dictionary."""
        # Arrange
        client = S3StorageClient()

        # Act
        kwargs = client._get_client_kwargs()

        # Assert
        assert isinstance(kwargs, dict)
        assert "service_name" in kwargs
        assert kwargs["service_name"] == "s3"
        assert "endpoint_url" in kwargs
        assert "aws_access_key_id" in kwargs
        assert "aws_secret_access_key" in kwargs
        assert "region_name" in kwargs

    @pytest.mark.asyncio
    async def test_upload_text_success(self) -> None:
        """Test that upload_text successfully uploads content to S3."""
        # Arrange
        client = S3StorageClient()
        mock_s3 = AsyncMock()
        mock_session = MagicMock()
        mock_session.client.return_value.__aenter__ = AsyncMock(return_value=mock_s3)
        mock_session.client.return_value.__aexit__ = AsyncMock(return_value=None)

        s3_key = "reports/test-report.md"
        content = "# Test Report"
        content_type = "text/markdown; charset=utf-8"

        # Act
        with patch.object(client, "_session", mock_session):
            result = await client.upload_text(s3_key, content, content_type)

        # Assert
        assert result == s3_key
        mock_s3.put_object.assert_called_once()
        call_kwargs = mock_s3.put_object.call_args[1]
        assert call_kwargs["Key"] == s3_key
        assert call_kwargs["Body"] == content.encode("utf-8")
        assert call_kwargs["ContentType"] == content_type

    @pytest.mark.asyncio
    async def test_upload_text_encodes_content_as_utf8(self) -> None:
        """Test that upload_text encodes content as UTF-8."""
        # Arrange
        client = S3StorageClient()
        mock_s3 = AsyncMock()
        mock_session = MagicMock()
        mock_session.client.return_value.__aenter__ = AsyncMock(return_value=mock_s3)
        mock_session.client.return_value.__aexit__ = AsyncMock(return_value=None)

        content = "# Relatório com acentuação"
        s3_key = "reports/test.md"
        content_type = "text/markdown; charset=utf-8"

        # Act
        with patch.object(client, "_session", mock_session):
            await client.upload_text(s3_key, content, content_type)

        # Assert
        call_kwargs = mock_s3.put_object.call_args[1]
        assert call_kwargs["Body"] == content.encode("utf-8")

    @pytest.mark.asyncio
    async def test_check_health_success(self) -> None:
        """Test that check_health returns True when S3 bucket is accessible."""
        # Arrange
        client = S3StorageClient()
        mock_s3 = AsyncMock()
        mock_session = MagicMock()
        mock_session.client.return_value.__aenter__ = AsyncMock(return_value=mock_s3)
        mock_session.client.return_value.__aexit__ = AsyncMock(return_value=None)

        # Act
        with patch.object(client, "_session", mock_session):
            result = await client.check_health()

        # Assert
        assert result is True
        mock_s3.head_bucket.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_health_failure(self) -> None:
        """Test that check_health returns False when S3 bucket is not accessible."""
        # Arrange
        client = S3StorageClient()
        mock_s3 = AsyncMock()
        mock_s3.head_bucket = AsyncMock(side_effect=Exception("Access denied"))
        mock_session = MagicMock()
        mock_session.client.return_value.__aenter__ = AsyncMock(return_value=mock_s3)
        mock_session.client.return_value.__aexit__ = AsyncMock(return_value=None)

        # Act
        with patch.object(client, "_session", mock_session):
            result = await client.check_health()

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_check_health_catches_all_exceptions(self) -> None:
        """Test that check_health catches any exception and returns False."""
        # Arrange
        client = S3StorageClient()
        mock_s3 = AsyncMock()
        mock_s3.head_bucket = AsyncMock(side_effect=RuntimeError("Network error"))
        mock_session = MagicMock()
        mock_session.client.return_value.__aenter__ = AsyncMock(return_value=mock_s3)
        mock_session.client.return_value.__aexit__ = AsyncMock(return_value=None)

        # Act
        with patch.object(client, "_session", mock_session):
            result = await client.check_health()

        # Assert
        assert result is False
