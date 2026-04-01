import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class DiagramaUploadResponse(BaseModel):
    """DTO de resposta para o upload de um diagrama (HTTP 202)."""

    analise_id: uuid.UUID = Field(..., description="ID da análise criada")
    status: str = Field(..., description="Status inicial da análise")
    criado_em: datetime = Field(..., description="Data de criação da análise")
