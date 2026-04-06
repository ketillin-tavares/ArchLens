import json
from typing import cast

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel

from src.domain.prompts import ANALYZER_SYSTEM_PROMPT, ANALYZER_USER_PROMPT_TEMPLATE
from src.domain.schemas import ComponenteSchema
from src.infrastructure.agents.schemas import AnalyzerResultSchema
from src.infrastructure.observability.logging import get_logger

logger = get_logger()


class AnalyzerAgent:
    """Agente responsável por identificar riscos arquiteturais (text-only)."""

    def __init__(self, model: OpenAIChatModel) -> None:
        self._agent = Agent(
            model=model,
            system_prompt=ANALYZER_SYSTEM_PROMPT,
            output_type=AnalyzerResultSchema,
        )

    async def run(
        self,
        componentes: list[ComponenteSchema],
        descricao_geral: str,
    ) -> AnalyzerResultSchema:
        """
        Analisa riscos com base nos componentes detectados e descrição textual.

        Args:
            componentes: Lista de componentes extraídos pelo Extractor Agent.
            descricao_geral: Descrição textual do diagrama produzida pelo Extractor.

        Returns:
            Riscos identificados com recomendações.
        """
        componentes_json = json.dumps(
            [c.model_dump(mode="json") for c in componentes],
            ensure_ascii=False,
            indent=2,
        )

        user_prompt = ANALYZER_USER_PROMPT_TEMPLATE.format(
            componentes_json=componentes_json,
            descricao_geral=descricao_geral,
        )

        result = await self._agent.run(user_prompt)
        analysis = cast(AnalyzerResultSchema, result.output)
        logger.info("analyzer_concluido", total_riscos=len(analysis.riscos))
        return analysis
