import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, Field


class Diagrama(BaseModel):
    """Entidade que representa um diagrama de arquitetura enviado pelo usuário."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, description="Identificador único do diagrama")
    nome_original: str = Field(..., description="Nome original do arquivo enviado")
    content_type: str = Field(..., description="MIME type do arquivo")
    tamanho_bytes: int = Field(..., gt=0, description="Tamanho do arquivo em bytes")
    storage_path: str = Field(..., description="Caminho do arquivo no S3/MinIO")
    criado_em: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Data de criação")
