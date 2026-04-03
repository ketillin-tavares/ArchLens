from enum import StrEnum

from pydantic import BaseModel, Field, field_validator, model_validator


class TipoComponente(StrEnum):
    """Tipos permitidos para componentes arquiteturais."""

    API_GATEWAY = "api_gateway"
    DATABASE = "database"
    QUEUE = "queue"
    SERVICE = "service"
    LOAD_BALANCER = "load_balancer"
    CACHE = "cache"
    STORAGE = "storage"
    OTHER = "other"


class Severidade(StrEnum):
    """Níveis de severidade para riscos e recomendações."""

    BAIXA = "baixa"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"


class ComponenteMetadata(BaseModel):
    """Metadata descritiva de um componente."""

    descricao: str = Field(..., min_length=1, max_length=500)


class ComponenteSchema(BaseModel):
    """Schema de validação para um componente identificado pelo LLM."""

    nome: str = Field(..., min_length=1, max_length=255)
    tipo: TipoComponente
    confianca: float = Field(..., ge=0.0, le=1.0)
    metadata: ComponenteMetadata

    @field_validator("confianca")
    @classmethod
    def round_confianca(cls, v: float) -> float:
        """Arredonda a confiança para 2 casas decimais."""
        return round(v, 2)


class RecomendacaoSchema(BaseModel):
    """Schema de validação para a recomendação de um risco."""

    descricao: str = Field(..., min_length=1, max_length=1000)
    prioridade: Severidade


class RiscoSchema(BaseModel):
    """Schema de validação para um risco identificado pelo LLM."""

    descricao: str = Field(..., min_length=1, max_length=1000)
    severidade: Severidade
    componentes_afetados: list[str] = Field(..., min_length=1)
    recomendacao: RecomendacaoSchema


class AnaliseResultSchema(BaseModel):
    """Schema raiz da resposta da IA — componentes e riscos."""

    componentes: list[ComponenteSchema] = Field(default_factory=list)
    riscos: list[RiscoSchema] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_risk_references(self) -> "AnaliseResultSchema":
        """Garante que cada risco referencia apenas componentes existentes."""
        nomes_componentes = {c.nome for c in self.componentes}
        for risco in self.riscos:
            refs_invalidas = [nome for nome in risco.componentes_afetados if nome not in nomes_componentes]
            if refs_invalidas:
                raise ValueError(
                    f"Risco '{risco.descricao}' referencia componentes "
                    f"inexistentes: {refs_invalidas}. "
                    f"Componentes válidos: {nomes_componentes}"
                )
        return self
