import structlog

from src.application.ports import LLMClient
from src.application.sanity_checks import check_sanity
from src.application.validation import validate_and_parse
from src.domain.schemas import AnaliseResultSchema

logger = structlog.get_logger()


class SingleCallPipeline:
    """Pipeline de chamada única ao LLM — comportamento original do sistema."""

    def __init__(self, llm_client: LLMClient) -> None:
        self._llm_client = llm_client

    async def run(self, image_b64: str) -> AnaliseResultSchema:
        """
        Executa análise via chamada única ao LLM (extração + riscos em um só prompt).

        Args:
            image_b64: Imagem do diagrama codificada em base64.

        Returns:
            Schema validado com componentes e riscos.
        """
        raw_response = await self._llm_client.analyze_image(image_b64)
        logger.info("single_call_resposta_recebida", response_length=len(raw_response))

        analise_result = await validate_and_parse(raw_response, self._llm_client)
        check_sanity(analise_result)

        return analise_result
