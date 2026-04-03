import uuid

from pydantic import BaseModel, Field


class Risco(BaseModel):
    """Entidade que representa um risco arquitetural identificado."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, description="Identificador único do risco")
    processamento_id: uuid.UUID = Field(..., description="ID do processamento associado")
    descricao: str = Field(..., description="Descrição do risco")
    severidade: str = Field(..., description="Severidade do risco (baixa, media, alta, critica)")
    recomendacao_descricao: str | None = Field(default=None, description="Descrição da recomendação")
    recomendacao_prioridade: str | None = Field(default=None, description="Prioridade da recomendação")
    componentes_afetados: list[str] = Field(default_factory=list, description="Nomes dos componentes afetados")
