from pydantic import BaseModel, Field


class NotFoundResponse(BaseModel):
    """Resposta de erro para recurso não encontrado (HTTP 404)."""

    detail: str = Field(
        default="Relatório ainda não gerado para esta análise",
        description="Mensagem de erro",
    )
