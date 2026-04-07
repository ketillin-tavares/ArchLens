import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class AnaliseResponse(BaseModel):
    """DTO de resposta para consulta de status de uma análise."""

    id: uuid.UUID = Field(..., description="ID da análise")
    diagrama_id: uuid.UUID = Field(..., description="ID do diagrama associado")
    status: str = Field(..., description="Status atual da análise")
    erro_detalhe: str | None = Field(default=None, description="Detalhes do erro, se houver")
    relatorio_s3_key: str | None = Field(default=None, description="Chave S3 do relatório Markdown (.md)")
    criado_em: datetime = Field(..., description="Data de criação da análise")
    atualizado_em: datetime = Field(..., description="Última atualização da análise")
