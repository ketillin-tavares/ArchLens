from pydantic import BaseModel, Field

from src.domain.exceptions import ArquivoInvalidoError, ArquivoTamanhoExcedidoError


class ArquivoDiagrama(BaseModel):
    """Value object representando um arquivo de diagrama recebido via upload."""

    nome_original: str = Field(..., description="Nome original do arquivo enviado")
    content_type: str = Field(..., description="MIME type do arquivo")
    tamanho_bytes: int = Field(..., gt=0, description="Tamanho do arquivo em bytes")
    conteudo: bytes = Field(..., exclude=True, description="Conteúdo binário do arquivo")

    model_config = {"arbitrary_types_allowed": True}

    TIPOS_PERMITIDOS: frozenset[str] = frozenset({"image/png", "image/jpeg", "application/pdf"})
    TAMANHO_MAXIMO_BYTES: int = 10 * 1024 * 1024  # 10MB

    def validar(self) -> None:
        """Valida tipo e tamanho do arquivo, lançando exceções de domínio se inválido."""
        if self.content_type not in self.TIPOS_PERMITIDOS:
            raise ArquivoInvalidoError("Tipo de arquivo não suportado. Use: image/png, image/jpeg, application/pdf")
        if self.tamanho_bytes > self.TAMANHO_MAXIMO_BYTES:
            raise ArquivoTamanhoExcedidoError("Arquivo excede o tamanho máximo de 10MB")

    @property
    def extensao(self) -> str:
        """Retorna a extensão do arquivo baseada no content_type."""
        mapa: dict[str, str] = {
            "image/png": "png",
            "image/jpeg": "jpeg",
            "application/pdf": "pdf",
        }
        return mapa.get(self.content_type, "bin")
