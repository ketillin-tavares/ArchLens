import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RelatorioResponse(BaseModel):
    """DTO de resposta para consulta de um relatório."""

    id: uuid.UUID = Field(..., description="ID do relatório")
    analise_id: uuid.UUID = Field(..., description="ID da análise que originou o relatório")
    titulo: str = Field(..., description="Título do relatório")
    resumo: str = Field(..., description="Resumo descritivo do relatório")
    conteudo: dict[str, Any] = Field(..., description="Conteúdo estruturado do relatório")
    criado_em: datetime = Field(..., description="Data de criação do relatório")
