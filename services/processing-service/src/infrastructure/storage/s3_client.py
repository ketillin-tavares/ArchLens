import aioboto3
import pybreaker
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from src.domain.exceptions import StorageDownloadError
from src.environment import get_settings
from src.infrastructure.observability.logging import get_logger

logger = get_logger()

storage_circuit_breaker = pybreaker.CircuitBreaker(
    fail_max=3,
    reset_timeout=30,
    name="s3_storage",
)


class S3StorageClient:
    """Cliente para download de arquivos do S3/LocalStack com circuit breaker e retry."""

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

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type(StorageDownloadError),
        reraise=True,
    )
    async def download_file(self, storage_path: str) -> bytes:
        """
        Faz download de um arquivo do S3 com circuit breaker e retry.

        Args:
            storage_path: Caminho (key) no bucket S3.

        Returns:
            Conteúdo binário do arquivo.

        Raises:
            StorageDownloadError: Se o download falhar após retries.
        """
        return await self._download_with_breaker(storage_path)

    @storage_circuit_breaker
    async def _download_with_breaker(self, storage_path: str) -> bytes:
        """Download protegido por circuit breaker."""
        try:
            async with self._session.client(**self._get_client_kwargs()) as s3:
                response = await s3.get_object(
                    Bucket=self._settings.bucket_name,
                    Key=storage_path,
                )
                data = await response["Body"].read()
            logger.info(
                "diagrama_download_s3_ok",
                storage_path=storage_path,
                bucket=self._settings.bucket_name,
            )
            return data
        except Exception as exc:
            raise StorageDownloadError(f"Falha ao baixar {storage_path}: {exc}") from exc

    async def check_health(self) -> bool:
        """Verifica se o bucket S3 está acessível."""
        try:
            async with self._session.client(**self._get_client_kwargs()) as s3:
                await s3.head_bucket(Bucket=self._settings.bucket_name)
            return True
        except Exception:
            return False
