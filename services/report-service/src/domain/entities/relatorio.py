import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class Relatorio(BaseModel):
    """Entidade que representa um relatório de análise arquitetural."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, description="Identificador único do relatório")
    analise_id: uuid.UUID = Field(..., description="ID da análise que originou o relatório")
    titulo: str = Field(..., description="Título do relatório")
    resumo: str = Field(..., description="Resumo descritivo do relatório")
    conteudo: dict[str, Any] = Field(
        ..., description="Conteúdo estruturado do relatório (componentes, riscos, estatísticas)"
    )
    s3_key: str | None = Field(
        default=None,
        description="Chave S3 do relatório Markdown (.md). None se a geração de Markdown falhou.",
    )
    criado_em: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Data de criação")
