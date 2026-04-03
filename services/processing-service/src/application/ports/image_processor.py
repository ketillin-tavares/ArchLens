import abc


class ImageProcessor(abc.ABC):
    """Port (interface) para normalização de imagens de diagramas."""

    @abc.abstractmethod
    def normalize(self, file_bytes: bytes, content_type: str) -> str:
        """
        Normaliza um arquivo de imagem/PDF para base64 PNG.

        Args:
            file_bytes: Conteúdo binário do arquivo.
            content_type: MIME type do arquivo (image/png, application/pdf, etc.).

        Returns:
            Imagem normalizada em base64.
        """
