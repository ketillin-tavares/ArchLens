import pybreaker
import structlog
from pydantic_ai import Agent
from pydantic_ai.messages import ImageUrl
from pydantic_ai.models.openai import OpenAIChatModel
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from src.domain.exceptions import (
    LLMApiError,
    LLMContentFilterError,
    LLMContextWindowError,
    LLMRateLimitError,
    LLMTimeoutError,
)
from src.domain.schemas import AnaliseResultSchema
from src.domain.value_objects import (
    CORRECTION_SYSTEM_PROMPT,
    CORRECTION_USER_PROMPT_TEMPLATE,
    SYSTEM_PROMPT,
    USER_PROMPT,
)
from src.environment import get_settings

logger = structlog.get_logger()

llm_circuit_breaker = pybreaker.CircuitBreaker(
    fail_max=3,
    reset_timeout=30,
    name="llm_api",
)


def _classify_llm_exception(exc: Exception) -> Exception:
    """
    Classifica exceções do LLM em tipos específicos.

    Args:
        exc: Exceção original.

    Returns:
        Exceção classificada.
    """
    error_msg = str(exc).lower()

    if "timeout" in error_msg or "timed out" in error_msg:
        return LLMTimeoutError(f"Timeout na chamada ao LLM: {exc}")
    if "429" in error_msg or "rate_limit" in error_msg or "rate limit" in error_msg:
        return LLMRateLimitError(f"Rate limit atingido: {exc}")
    if "content_filter" in error_msg or "safety" in error_msg or "content_policy" in error_msg:
        return LLMContentFilterError(f"Conteúdo bloqueado pelo filtro: {exc}")
    if "context_length" in error_msg or "maximum context" in error_msg or "token limit" in error_msg:
        return LLMContextWindowError(f"Contexto excedeu o limite: {exc}")

    return LLMApiError(f"Erro na API do LLM: {exc}")


class PydanticAILLMClient:
    """Client para o LLM via PydanticAI, apontando para LiteLLM Proxy."""

    def __init__(self) -> None:
        settings = get_settings().llm
        self._model = OpenAIChatModel(
            model_name=settings.model_name,
            provider="openai",
            base_url=settings.base_url,
            api_key=settings.api_key,
        )  # type: ignore
        self._temperature = settings.temperature
        self._max_tokens = settings.max_tokens

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type(LLMApiError),
        reraise=True,
    )
    async def analyze_image(self, image_b64: str) -> str:
        """
        Envia imagem ao LLM para análise arquitetural com circuit breaker e retry.

        Args:
            image_b64: Imagem em base64.

        Returns:
            String JSON com a resposta do LLM.
        """
        return await self._analyze_with_breaker(image_b64)

    @llm_circuit_breaker
    async def _analyze_with_breaker(self, image_b64: str) -> str:
        """Chamada ao LLM protegida por circuit breaker."""
        try:
            agent = Agent(
                model=self._model,
                system_prompt=SYSTEM_PROMPT,
                result_type=AnaliseResultSchema,
            )  # type: ignore

            result = await agent.run(
                [
                    USER_PROMPT,
                    ImageUrl(url=f"data:image/png;base64,{image_b64}"),
                ]
            )
            return result.model_dump_json()  # type: ignore
        except Exception as exc:
            classified = _classify_llm_exception(exc)
            raise classified from exc

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(LLMApiError),
        reraise=True,
    )
    async def correct_json(self, original_json: str, validation_errors: str) -> str:
        """
        Envia JSON com erros ao LLM para correção.

        Args:
            original_json: JSON original com erros.
            validation_errors: Descrição dos erros de validação.

        Returns:
            String JSON corrigida.
        """
        try:
            agent = Agent(
                model=self._model,
                system_prompt=CORRECTION_SYSTEM_PROMPT,
                result_type=AnaliseResultSchema,
            )  # type: ignore

            user_message = CORRECTION_USER_PROMPT_TEMPLATE.format(
                original_json=original_json,
                validation_errors=validation_errors,
            )

            result = await agent.run(user_message)
            return result.model_dump_json()  # type: ignore
        except Exception as exc:
            classified = _classify_llm_exception(exc)
            raise classified from exc
