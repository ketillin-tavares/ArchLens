from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from src.application.ports import AnalysisPipeline, LLMClient
from src.domain.schemas import AnaliseResultSchema
from src.environment import get_settings
from src.infrastructure.agents import MultiAgentPipeline, SingleCallPipeline


class SingleCallPipelineGateway(AnalysisPipeline):
    """Adapter que implementa AnalysisPipeline usando chamada única ao LLM."""

    def __init__(self, llm_client: LLMClient) -> None:
        self._pipeline = SingleCallPipeline(llm_client=llm_client)

    async def run(self, image_b64: str) -> AnaliseResultSchema:
        """
        Executa análise via chamada única.

        Args:
            image_b64: Imagem em base64.

        Returns:
            Schema validado com componentes e riscos.
        """
        return await self._pipeline.run(image_b64)


class MultiAgentPipelineGateway(AnalysisPipeline):
    """Adapter que implementa AnalysisPipeline usando pipeline multi-agent."""

    def __init__(self) -> None:
        settings = get_settings()
        llm = settings.llm

        provider = OpenAIProvider(
            base_url=llm.base_url,
            api_key=llm.api_key,
        )

        vision_model = OpenAIChatModel(
            model_name=llm.model_name,
            provider=provider,
        )

        analyzer_model = OpenAIChatModel(
            model_name=llm.analyzer_model_name,
            provider=provider,
        )

        self._pipeline = MultiAgentPipeline(
            vision_model=vision_model,
            analyzer_model=analyzer_model,
            enable_judge=settings.multiagent.enable_judge,
        )

    async def run(self, image_b64: str) -> AnaliseResultSchema:
        """
        Executa análise via pipeline multi-agent.

        Args:
            image_b64: Imagem em base64.

        Returns:
            Schema validado com componentes e riscos.
        """
        return await self._pipeline.run(image_b64)
