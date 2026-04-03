import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ComponenteResponse(BaseModel):
    """DTO de resposta para um componente."""

    id: uuid.UUID = Field(..., description="ID do componente")
    nome: str = Field(..., description="Nome do componente")
    tipo: str = Field(..., description="Tipo do componente")
    confianca: float = Field(..., description="Score de confiança")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Metadata do componente")


class RiscoResponse(BaseModel):
    """DTO de resposta para um risco."""

    id: uuid.UUID = Field(..., description="ID do risco")
    descricao: str = Field(..., description="Descrição do risco")
    severidade: str = Field(..., description="Severidade do risco")
    componentes_afetados: list[str] = Field(default_factory=list, description="Componentes afetados")
    recomendacao: dict[str, str] = Field(default_factory=dict, description="Recomendação")


class ProcessamentoResponse(BaseModel):
    """DTO de resposta para consulta de processamento."""

    analise_id: uuid.UUID = Field(..., description="ID da análise")
    status: str = Field(..., description="Status do processamento")
    iniciado_em: datetime | None = Field(default=None, description="Timestamp de início")
    concluido_em: datetime | None = Field(default=None, description="Timestamp de conclusão")
    componentes: list[ComponenteResponse] = Field(default_factory=list, description="Componentes identificados")
    riscos: list[RiscoResponse] = Field(default_factory=list, description="Riscos identificados")
