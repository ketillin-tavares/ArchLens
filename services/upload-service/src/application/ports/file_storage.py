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
