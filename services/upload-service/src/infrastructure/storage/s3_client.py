import aioboto3
import pybreaker
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from src.environment import get_settings

logger = structlog.get_logger()

storage_circuit_breaker = pybreaker.CircuitBreaker(
    fail_max=3,
    reset_timeout=30,
    name="s3_storage",
)


class S3StorageClient:
    """Cliente para operações de armazenamento no S3/MinIO com circuit breaker."""

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

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def upload_file(self, file_bytes: bytes, storage_path: str, content_type: str) -> str:
        """
        Faz upload de um arquivo para o S3/MinIO.

        Args:
            file_bytes: Conteúdo binário do arquivo.
            storage_path: Caminho (key) no bucket S3.
            content_type: MIME type do arquivo.

        Returns:
            O storage_path do arquivo armazenado.

        Raises:
            pybreaker.CircuitBreakerError: Se o circuit breaker estiver aberto.
        """
        return await self._upload_with_breaker(file_bytes, storage_path, content_type)

    @storage_circuit_breaker
    async def _upload_with_breaker(self, file_bytes: bytes, storage_path: str, content_type: str) -> str:
        """Upload protegido por circuit breaker."""
        async with self._session.client(**self._get_client_kwargs()) as s3:
            await s3.put_object(
                Bucket=self._settings.bucket_name,
                Key=storage_path,
                Body=file_bytes,
                ContentType=content_type,
            )
        logger.info(
            "diagrama_upload_s3_ok",
            storage_path=storage_path,
            bucket=self._settings.bucket_name,
        )
        return storage_path

    async def download_file(self, storage_path: str) -> bytes:
        """
        Faz download de um arquivo do S3/MinIO.

        Args:
            storage_path: Caminho (key) no bucket S3.

        Returns:
            Conteúdo binário do arquivo.
        """
        async with self._session.client(**self._get_client_kwargs()) as s3:
            response = await s3.get_object(
                Bucket=self._settings.bucket_name,
                Key=storage_path,
            )
            return await response["Body"].read()

    async def check_health(self) -> bool:
        """Verifica se o bucket S3 está acessível."""
        try:
            async with self._session.client(**self._get_client_kwargs()) as s3:
                await s3.head_bucket(Bucket=self._settings.bucket_name)
            return True
        except Exception:
            return False
