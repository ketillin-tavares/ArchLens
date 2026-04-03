"""Unit tests for S3 storage client."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.domain.exceptions import StorageDownloadError
from src.infrastructure.storage.s3_client import S3StorageClient


class TestS3StorageClient:
    """Tests for S3StorageClient."""

    def test_s3_storage_client_initialization(self) -> None:
        """Test S3StorageClient initializes correctly."""
        # Arrange & Act
        with patch("src.infrastructure.storage.s3_client.get_settings") as mock_settings:
            mock_s3_settings = MagicMock()
            mock_s3_settings.endpoint_url = "http://localhost:4566"
            mock_s3_settings.access_key_id = "test"
            mock_s3_settings.secret_access_key = "test"
            mock_s3_settings.region_name = "us-east-1"
            mock_s3_settings.bucket_name = "test-bucket"

            mock_settings.return_value.s3 = mock_s3_settings

            client = S3StorageClient()

            # Assert
            assert client is not None
            assert client._settings == mock_s3_settings

    def test_get_client_kwargs(self) -> None:
        """Test _get_client_kwargs returns correct configuration."""
        # Arrange
        with patch("src.infrastructure.storage.s3_client.get_settings") as mock_settings:
            mock_s3_settings = MagicMock()
            mock_s3_settings.endpoint_url = "http://localhost:4566"
            mock_s3_settings.access_key_id = "test-key"
            mock_s3_settings.secret_access_key = "test-secret"
            mock_s3_settings.region_name = "us-east-1"
            mock_s3_settings.bucket_name = "test-bucket"

            mock_settings.return_value.s3 = mock_s3_settings

            client = S3StorageClient()

            # Act
            kwargs = client._get_client_kwargs()

            # Assert
            assert kwargs["service_name"] == "s3"
            assert kwargs["endpoint_url"] == "http://localhost:4566"
            assert kwargs["aws_access_key_id"] == "test-key"
            assert kwargs["aws_secret_access_key"] == "test-secret"
            assert kwargs["region_name"] == "us-east-1"

    @pytest.mark.asyncio
    async def test_download_file_success(self) -> None:
        """Test successful file download."""
        # Arrange
        with patch("src.infrastructure.storage.s3_client.get_settings") as mock_settings:
            mock_s3_settings = MagicMock()
            mock_s3_settings.endpoint_url = "http://localhost:4566"
            mock_s3_settings.access_key_id = "test"
            mock_s3_settings.secret_access_key = "test"
            mock_s3_settings.region_name = "us-east-1"
            mock_s3_settings.bucket_name = "test-bucket"

            mock_settings.return_value.s3 = mock_s3_settings

            client = S3StorageClient()

            # Mock the session and S3 client
            with patch.object(client, "_download_with_breaker", new_callable=AsyncMock) as mock_download:
                file_content = b"test file content"
                mock_download.return_value = file_content

                # Act
                result = await client.download_file("path/to/file.png")

                # Assert
                assert result == file_content
                mock_download.assert_called_once_with("path/to/file.png")

    @pytest.mark.asyncio
    async def test_download_file_error(self) -> None:
        """Test download raises StorageDownloadError on failure."""
        # Arrange
        with patch("src.infrastructure.storage.s3_client.get_settings") as mock_settings:
            mock_s3_settings = MagicMock()
            mock_s3_settings.endpoint_url = "http://localhost:4566"
            mock_s3_settings.access_key_id = "test"
            mock_s3_settings.secret_access_key = "test"
            mock_s3_settings.region_name = "us-east-1"
            mock_s3_settings.bucket_name = "test-bucket"

            mock_settings.return_value.s3 = mock_s3_settings

            client = S3StorageClient()

            # Mock the breaker to raise error
            with patch.object(client, "_download_with_breaker", new_callable=AsyncMock) as mock_download:
                mock_download.side_effect = StorageDownloadError("Download failed")

                # Act & Assert
                with pytest.raises(StorageDownloadError):
                    await client.download_file("path/to/file.png")

    @pytest.mark.asyncio
    async def test_check_health_success(self) -> None:
        """Test check_health returns True when bucket is accessible."""
        # Arrange
        with patch("src.infrastructure.storage.s3_client.get_settings") as mock_settings:
            mock_s3_settings = MagicMock()
            mock_s3_settings.endpoint_url = "http://localhost:4566"
            mock_s3_settings.access_key_id = "test"
            mock_s3_settings.secret_access_key = "test"
            mock_s3_settings.region_name = "us-east-1"
            mock_s3_settings.bucket_name = "test-bucket"

            mock_settings.return_value.s3 = mock_s3_settings

            client = S3StorageClient()

            # Mock aioboto3 session
            mock_s3_client = AsyncMock()
            mock_s3_client.head_bucket = AsyncMock()
            mock_s3_client.__aenter__.return_value = mock_s3_client
            mock_s3_client.__aexit__.return_value = None

            with patch.object(client._session, "client", return_value=mock_s3_client):
                # Act
                result = await client.check_health()

                # Assert
                assert result is True

    @pytest.mark.asyncio
    async def test_check_health_failure(self) -> None:
        """Test check_health returns False when bucket is not accessible."""
        # Arrange
        with patch("src.infrastructure.storage.s3_client.get_settings") as mock_settings:
            mock_s3_settings = MagicMock()
            mock_s3_settings.endpoint_url = "http://localhost:4566"
            mock_s3_settings.access_key_id = "test"
            mock_s3_settings.secret_access_key = "test"
            mock_s3_settings.region_name = "us-east-1"
            mock_s3_settings.bucket_name = "test-bucket"

            mock_settings.return_value.s3 = mock_s3_settings

            client = S3StorageClient()

            # Mock aioboto3 session to raise error
            mock_s3_client = AsyncMock()
            mock_s3_client.head_bucket = AsyncMock(side_effect=Exception("Connection refused"))
            mock_s3_client.__aenter__.return_value = mock_s3_client
            mock_s3_client.__aexit__.return_value = None

            with patch.object(client._session, "client", return_value=mock_s3_client):
                # Act
                result = await client.check_health()

                # Assert
                assert result is False

    @pytest.mark.asyncio
    async def test_download_with_breaker_success(self) -> None:
        """Test _download_with_breaker successfully downloads file."""
        # Arrange
        with patch("src.infrastructure.storage.s3_client.get_settings") as mock_settings:
            mock_s3_settings = MagicMock()
            mock_s3_settings.endpoint_url = "http://localhost:4566"
            mock_s3_settings.access_key_id = "test"
            mock_s3_settings.secret_access_key = "test"
            mock_s3_settings.region_name = "us-east-1"
            mock_s3_settings.bucket_name = "test-bucket"

            mock_settings.return_value.s3 = mock_s3_settings

            client = S3StorageClient()

            # Mock aioboto3 session
            mock_body = AsyncMock()
            mock_body.read = AsyncMock(return_value=b"file content")
            mock_response = {"Body": mock_body}

            mock_s3_client = AsyncMock()
            mock_s3_client.get_object = AsyncMock(return_value=mock_response)
            mock_s3_client.__aenter__.return_value = mock_s3_client
            mock_s3_client.__aexit__.return_value = None

            with patch.object(client._session, "client", return_value=mock_s3_client):
                # Act
                result = await client._download_with_breaker("path/to/file.png")

                # Assert
                assert result == b"file content"

    @pytest.mark.asyncio
    async def test_download_with_breaker_error(self) -> None:
        """Test _download_with_breaker raises error on S3 failure."""
        # Arrange
        with patch("src.infrastructure.storage.s3_client.get_settings") as mock_settings:
            mock_s3_settings = MagicMock()
            mock_s3_settings.endpoint_url = "http://localhost:4566"
            mock_s3_settings.access_key_id = "test"
            mock_s3_settings.secret_access_key = "test"
            mock_s3_settings.region_name = "us-east-1"
            mock_s3_settings.bucket_name = "test-bucket"

            mock_settings.return_value.s3 = mock_s3_settings

            client = S3StorageClient()

            # Mock aioboto3 session to raise error
            mock_s3_client = AsyncMock()
            mock_s3_client.get_object = AsyncMock(side_effect=Exception("S3 error"))
            mock_s3_client.__aenter__.return_value = mock_s3_client
            mock_s3_client.__aexit__.return_value = None

            with patch.object(client._session, "client", return_value=mock_s3_client):
                # Act & Assert
                with pytest.raises(StorageDownloadError):
                    await client._download_with_breaker("path/to/file.png")
