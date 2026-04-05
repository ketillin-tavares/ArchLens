from src.application.ports import FileStorage
from src.infrastructure.storage.s3_client import S3StorageClient


class S3FileStorageGateway(FileStorage):
    """Adapter que implementa FileStorage usando S3/MinIO."""

    def __init__(self, client: S3StorageClient | None = None) -> None:
        self._client = client or S3StorageClient()

    async def upload_text(self, s3_key: str, content: str, content_type: str) -> str:
        """
        Faz upload de conteúdo textual para o S3.

        Args:
            s3_key: Chave (path) no bucket S3.
            content: Conteúdo textual a ser armazenado.
            content_type: MIME type do arquivo.

        Returns:
            A s3_key do arquivo armazenado.
        """
        return await self._client.upload_text(s3_key, content, content_type)

    async def check_health(self) -> bool:
        """
        Verifica se o bucket S3 está acessível.

        Returns:
            True se acessível, False caso contrário.
        """
        return await self._client.check_health()
