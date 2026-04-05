import abc


class FileStorage(abc.ABC):
    """Port (interface) para armazenamento de arquivos."""

    @abc.abstractmethod
    async def upload_file(self, file_bytes: bytes, storage_path: str, content_type: str) -> str:
        """
        Faz upload de um arquivo para o storage.

        Args:
            file_bytes: Conteúdo binário do arquivo.
            storage_path: Caminho de destino.
            content_type: MIME type do arquivo.

        Returns:
            Caminho do arquivo armazenado.
        """

    @abc.abstractmethod
    async def generate_presigned_url(self, s3_key: str, expires_in: int = 3600) -> str:
        """
        Gera URL pré-assinada para download de um arquivo do S3.

        Args:
            s3_key: Chave (path) do arquivo no bucket S3.
            expires_in: Tempo de expiração em segundos (padrão: 3600).

        Returns:
            URL pré-assinada para download direto.
        """
