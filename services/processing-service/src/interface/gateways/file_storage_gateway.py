from src.application.ports import FileStorage
from src.infrastructure.storage import S3StorageClient


class S3FileStorageGateway(FileStorage):
    """Adapter que implementa FileStorage usando S3StorageClient."""

    def __init__(self, s3_client: S3StorageClient) -> None:
        self._s3_client = s3_client

    async def download_file(self, storage_path: str) -> bytes:
        """
        Faz download de um arquivo do S3.

        Args:
            storage_path: Caminho (key) do arquivo no bucket.

        Returns:
            Conteúdo binário do arquivo.
        """
        return await self._s3_client.download_file(storage_path)
