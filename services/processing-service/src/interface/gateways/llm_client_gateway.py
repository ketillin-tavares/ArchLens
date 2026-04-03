from src.application.ports import LLMClient
from src.infrastructure.llm import PydanticAILLMClient


class PydanticAILLMClientGateway(LLMClient):
    """Adapter que implementa LLMClient usando PydanticAILLMClient."""

    def __init__(self) -> None:
        self._client = PydanticAILLMClient()

    async def analyze_image(self, image_b64: str) -> str:
        """
        Envia imagem ao LLM para análise arquitetural.

        Args:
            image_b64: Imagem em base64.

        Returns:
            String JSON com a resposta.
        """
        return await self._client.analyze_image(image_b64)

    async def correct_json(self, original_json: str, validation_errors: str) -> str:
        """
        Envia JSON com erros ao LLM para correção.

        Args:
            original_json: JSON original com erros.
            validation_errors: Descrição dos erros.

        Returns:
            String JSON corrigida.
        """
        return await self._client.correct_json(original_json, validation_errors)
