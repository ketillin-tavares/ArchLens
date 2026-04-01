from pydantic import BaseModel, Field


class ArquivoInvalidoResponse(BaseModel):
    """Resposta de erro para arquivo com tipo não suportado (HTTP 400)."""

    detail: str = Field(
        default="Tipo de arquivo não suportado. Use: image/png, image/jpeg, application/pdf",
        description="Mensagem de erro",
    )


class ArquivoTamanhoExcedidoResponse(BaseModel):
    """Resposta de erro para arquivo que excede o tamanho máximo (HTTP 413)."""

    detail: str = Field(
        default="Arquivo excede o tamanho máximo de 10MB",
        description="Mensagem de erro",
    )


class NotFoundResponse(BaseModel):
    """Resposta de erro para recurso não encontrado (HTTP 404)."""

    detail: str = Field(
        default="Análise não encontrada",
        description="Mensagem de erro",
    )
