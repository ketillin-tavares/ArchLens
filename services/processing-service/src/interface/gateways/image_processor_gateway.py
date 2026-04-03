from src.application.ports import ImageProcessor
from src.infrastructure.image import FitzImageProcessor


class FitzImageProcessorGateway(ImageProcessor):
    """Adapter que implementa ImageProcessor usando FitzImageProcessor."""

    def __init__(self) -> None:
        self._processor = FitzImageProcessor()

    def normalize(self, file_bytes: bytes, content_type: str) -> str:
        """
        Normaliza um arquivo de imagem/PDF para base64 PNG.

        Args:
            file_bytes: Conteúdo binário do arquivo.
            content_type: MIME type do arquivo.

        Returns:
            Imagem normalizada em base64.
        """
        return self._processor.normalize(file_bytes, content_type)
