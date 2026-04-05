from typing import cast

import structlog
from pydantic_ai import Agent
from pydantic_ai.messages import ImageUrl
from pydantic_ai.models.openai import OpenAIChatModel

from src.domain.prompts import JUDGE_SYSTEM_PROMPT, JUDGE_USER_PROMPT_TEMPLATE
from src.domain.schemas import AnaliseResultSchema
from src.infrastructure.agents.schemas import JudgeResultSchema

logger = structlog.get_logger()


class JudgeAgent:
    """Agente responsável por avaliar a qualidade da análise (vision)."""

    def __init__(self, model: OpenAIChatModel) -> None:
        self._agent = Agent(
            model=model,
            system_prompt=JUDGE_SYSTEM_PROMPT,
            output_type=JudgeResultSchema,
        )

    async def run(
        self,
        analise_result: AnaliseResultSchema,
        image_b64: str,
    ) -> JudgeResultSchema:
        """
        Avalia a qualidade da análise comparando com a imagem original.

        Args:
            analise_result: Resultado combinado (componentes + riscos).
            image_b64: Imagem original em base64 para comparação.

        Returns:
            Scores de qualidade e veredito de aprovação.
        """
        analise_json = analise_result.model_dump_json(indent=2)

        user_prompt = JUDGE_USER_PROMPT_TEMPLATE.format(analise_json=analise_json)

        result = await self._agent.run(
            [
                user_prompt,
                ImageUrl(url=f"data:image/png;base64,{image_b64}"),
            ]
        )
        judgement = cast(JudgeResultSchema, result.output)
        logger.info(
            "judge_concluido",
            score_medio=judgement.score_medio,
            aprovado=judgement.aprovado,
            scores=judgement.scores,
        )
        return judgement
