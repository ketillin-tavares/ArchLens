import abc


class FileStorage(abc.ABC):
    """Port (interface) para armazenamento de arquivos no S3."""

    @abc.abstractmethod
    async def upload_text(self, s3_key: str, content: str, content_type: str) -> str:
        """
        Faz upload de conteúdo textual para o S3.

        Args:
            s3_key: Chave (path) no bucket S3.
            content: Conteúdo textual a ser armazenado.
            content_type: MIME type do arquivo (ex: 'text/markdown; charset=utf-8').

        Returns:
            A s3_key do arquivo armazenado.
        """

    @abc.abstractmethod
    async def check_health(self) -> bool:
        """
        Verifica se o bucket S3 está acessível.

        Returns:
            True se acessível, False caso contrário.
        """
