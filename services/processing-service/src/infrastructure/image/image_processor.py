import base64
import io

import fitz
from PIL import Image

from src.domain.exceptions import ImageProcessingError
from src.infrastructure.observability.logging import get_logger

logger = get_logger()

MAX_DIMENSION: int = 2048


class FitzImageProcessor:
    """Processador de imagens que normaliza diagramas para envio ao LLM."""

    def normalize(self, file_bytes: bytes, content_type: str) -> str:
        """
        Converte arquivo para imagem base64 normalizada (PNG, max 2048x2048).

        Args:
            file_bytes: Conteúdo binário do arquivo.
            content_type: MIME type do arquivo.

        Returns:
            Imagem normalizada em base64.

        Raises:
            ImageProcessingError: Se a normalização falhar.
        """
        try:
            if content_type == "application/pdf":
                img = self._pdf_to_image(file_bytes)
            else:
                img = Image.open(io.BytesIO(file_bytes))

            img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.Resampling.LANCZOS)

            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            return base64.b64encode(buffer.getvalue()).decode("utf-8")

        except ImageProcessingError:
            raise
        except Exception as exc:
            raise ImageProcessingError(f"Falha ao normalizar imagem: {exc}") from exc

    @staticmethod
    def _pdf_to_image(file_bytes: bytes) -> Image.Image:
        """
        Converte a primeira página de um PDF em imagem PIL.

        Args:
            file_bytes: Conteúdo binário do PDF.

        Returns:
            Imagem PIL da primeira página.
        """
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        page = doc[0]
        pix = page.get_pixmap(dpi=200)
        return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
