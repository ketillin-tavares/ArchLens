import uuid

from pydantic import BaseModel, Field


class DownloadRelatorioResponse(BaseModel):
    """DTO de resposta para geração de URL pré-assinada de download do relatório Markdown."""

    analise_id: uuid.UUID = Field(..., description="ID da análise")
    download_url: str = Field(..., description="URL pré-assinada para download do relatório Markdown")
    expires_in_seconds: int = Field(..., description="Tempo de expiração da URL em segundos")
    formato: str = Field(default="text/markdown", description="MIME type do arquivo disponível para download")
