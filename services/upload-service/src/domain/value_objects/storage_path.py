from uuid import UUID

from pydantic import BaseModel, Field


class StoragePath(BaseModel):
    """Value object representando o caminho de armazenamento no S3."""

    diagrama_id: UUID
    path: str = Field(..., description="Caminho completo no S3")
