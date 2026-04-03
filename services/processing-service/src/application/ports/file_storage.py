import abc


class FileStorage(abc.ABC):
    """Port (interface) para download de arquivos do storage."""

    @abc.abstractmethod
    async def download_file(self, storage_path: str) -> bytes:
        """
        Faz download de um arquivo do storage.

        Args:
            storage_path: Caminho (key) do arquivo no storage.

        Returns:
            Conteúdo binário do arquivo.
        """
