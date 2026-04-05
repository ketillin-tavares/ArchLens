from pydantic import BaseModel, Field

from src.domain.schemas import ComponenteSchema, RiscoSchema


class ExtractionResultSchema(BaseModel):
    """Schema de saída do Extractor Agent — componentes detectados + descrição textual."""

    componentes: list[ComponenteSchema] = Field(default_factory=list)
    descricao_geral: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Descrição textual detalhada do diagrama para o Analyzer Agent",
    )


class AnalyzerResultSchema(BaseModel):
    """Schema de saída do Analyzer Agent — riscos identificados."""

    riscos: list[RiscoSchema] = Field(default_factory=list)


class JudgeResultSchema(BaseModel):
    """Schema de saída do Judge Agent — avaliação de qualidade."""

    scores: dict[str, float] = Field(
        ...,
        description="Scores 0-10: completude, precisao, classificacao, riscos_relevantes",
    )
    score_medio: float = Field(..., ge=0.0, le=10.0)
    aprovado: bool
    comentario: str = Field(..., min_length=1, max_length=2000)
