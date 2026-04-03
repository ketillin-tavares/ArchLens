from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Resposta do endpoint de health check."""

    status: str = Field(..., description="Status geral do serviço")
    service: str = Field(..., description="Nome do serviço")
    dependencies: dict[str, str] = Field(..., description="Status de cada dependência")
