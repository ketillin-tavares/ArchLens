import uuid

from pydantic import BaseModel, Field


class Componente(BaseModel):
    """Entidade que representa um componente arquitetural identificado."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, description="Identificador único do componente")
    processamento_id: uuid.UUID = Field(..., description="ID do processamento associado")
    nome: str = Field(..., description="Nome/label do componente")
    tipo: str = Field(..., description="Tipo do componente (api_gateway, database, etc.)")
    confianca: float = Field(default=0.0, description="Score de confiança (0.0 a 1.0)")
    metadata: dict = Field(default_factory=dict, description="Metadata adicional do componente")
