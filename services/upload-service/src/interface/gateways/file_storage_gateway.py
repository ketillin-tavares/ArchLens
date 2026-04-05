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

    async def generate_presigned_url(self, s3_key: str, expires_in: int = 3600) -> str:
        """
        Gera URL pré-assinada para download de um arquivo do S3.

        Args:
            s3_key: Chave (path) do arquivo no bucket S3.
            expires_in: Tempo de expiração em segundos.

        Returns:
            URL pré-assinada para download direto.
        """
        return await self._client.generate_presigned_url(s3_key, expires_in)
