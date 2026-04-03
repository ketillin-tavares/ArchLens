import abc


class LLMClient(abc.ABC):
    """Port (interface) para interação com o LLM via vision."""

    @abc.abstractmethod
    async def analyze_image(self, image_b64: str) -> str:
        """
        Envia imagem base64 ao LLM e retorna a resposta raw JSON.

        Args:
            image_b64: Imagem codificada em base64.

        Returns:
            String JSON com a resposta do LLM.
        """

    @abc.abstractmethod
    async def correct_json(self, original_json: str, validation_errors: str) -> str:
        """
        Envia JSON com erros ao LLM para correção.

        Args:
            original_json: JSON original com erros.
            validation_errors: Descrição dos erros de validação.

        Returns:
            String JSON corrigida.
        """
