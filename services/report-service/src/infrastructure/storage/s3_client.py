import aioboto3
import structlog

from src.environment import get_settings

logger = structlog.get_logger()


class S3StorageClient:
    """Cliente para operações de armazenamento textual no S3/MinIO."""

    def __init__(self) -> None:
        self._settings = get_settings().s3
        self._session = aioboto3.Session()

    def _get_client_kwargs(self) -> dict:
        """Retorna os kwargs de configuração para o cliente S3."""
        return {
            "service_name": "s3",
            "endpoint_url": self._settings.endpoint_url,
            "aws_access_key_id": self._settings.access_key_id,
            "aws_secret_access_key": self._settings.secret_access_key,
            "region_name": self._settings.region_name,
        }

    async def upload_text(self, s3_key: str, content: str, content_type: str) -> str:
        """
        Faz upload de conteúdo textual para o S3.

        Args:
            s3_key: Chave (path) no bucket S3.
            content: Conteúdo textual a ser armazenado.
            content_type: MIME type (ex: 'text/markdown; charset=utf-8').

        Returns:
            A s3_key do arquivo armazenado.
        """
        async with self._session.client(**self._get_client_kwargs()) as s3:
            await s3.put_object(
                Bucket=self._settings.bucket_name,
                Key=s3_key,
                Body=content.encode("utf-8"),
                ContentType=content_type,
            )

        logger.info(
            "s3_upload_ok",
            s3_key=s3_key,
            bucket=self._settings.bucket_name,
            content_type=content_type,
        )

        return s3_key

    async def check_health(self) -> bool:
        """
        Verifica se o bucket S3 está acessível.

        Returns:
            True se acessível, False caso contrário.
        """
        try:
            async with self._session.client(**self._get_client_kwargs()) as s3:
                await s3.head_bucket(Bucket=self._settings.bucket_name)
            return True
        except Exception:
            return False
