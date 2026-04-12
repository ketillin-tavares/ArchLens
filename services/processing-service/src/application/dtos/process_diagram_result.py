from pydantic import BaseModel, Field


class ProcessDiagramResult(BaseModel):
    """Resultado resumido do processamento de um diagrama de arquitetura."""

    status: str = Field(..., description="'sucesso' ou 'falha'")
    total_componentes: int = Field(default=0, description="Total de componentes identificados")
    total_riscos: int = Field(default=0, description="Total de riscos identificados")
    avg_confianca: float = Field(default=0.0, description="Confiança média dos componentes (0.0 a 1.0)")
    erro: str | None = Field(default=None, description="Mensagem de erro, se houver falha")
    tipo_erro: str | None = Field(default=None, description="Tipo do erro (nome da exception), se houver")
