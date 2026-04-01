from src.application.ports import FileStorage
from src.infrastructure.storage.s3_client import S3StorageClient


class S3FileStorageGateway(FileStorage):
    """Adapter que implementa FileStorage usando S3/MinIO."""

    def __init__(self, client: S3StorageClient | None = None) -> None:
        self._client = client or S3StorageClient()

    async def upload_file(self, file_bytes: bytes, storage_path: str, content_type: str) -> str:
        """
        Faz upload de um arquivo para o S3/MinIO.

        Args:
            file_bytes: Conteúdo binário do arquivo.
            storage_path: Caminho de destino no bucket.
            content_type: MIME type do arquivo.

        Returns:
            Caminho do arquivo armazenado.
        """
        return await self._client.upload_file(file_bytes, storage_path, content_type)
