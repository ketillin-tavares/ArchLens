from typing import cast

import structlog
from pydantic_ai import Agent
from pydantic_ai.messages import ImageUrl
from pydantic_ai.models.openai import OpenAIChatModel

from src.domain.prompts import EXTRACTOR_SYSTEM_PROMPT, EXTRACTOR_USER_PROMPT
from src.infrastructure.agents.schemas import ExtractionResultSchema

logger = structlog.get_logger()


class ExtractorAgent:
    """Agente responsável por extrair componentes visíveis do diagrama (vision)."""

    def __init__(self, model: OpenAIChatModel) -> None:
        self._agent = Agent(
            model=model,
            system_prompt=EXTRACTOR_SYSTEM_PROMPT,
            output_type=ExtractionResultSchema,
        )

    async def run(self, image_b64: str) -> ExtractionResultSchema:
        """
        Analisa a imagem do diagrama e extrai componentes.

        Args:
            image_b64: Imagem codificada em base64.

        Returns:
            Componentes detectados e descrição textual do diagrama.
        """
        result = await self._agent.run(
            [
                EXTRACTOR_USER_PROMPT,
                ImageUrl(url=f"data:image/png;base64,{image_b64}"),
            ]
        )
        extraction = cast(ExtractionResultSchema, result.output)
        logger.info(
            "extractor_concluido",
            total_componentes=len(extraction.componentes),
            descricao_length=len(extraction.descricao_geral),
        )
        return extraction
