import json

import structlog

from src.application.ports import LLMClient
from src.domain.exceptions import SchemaValidationError
from src.domain.schemas import AnaliseResultSchema

logger = structlog.get_logger()


async def validate_and_parse(raw_response: str, llm_client: LLMClient) -> AnaliseResultSchema:
    """
    Valida a resposta raw do LLM e retorna o schema tipado.

    Tenta parsear diretamente. Se falhar, faz uma chamada de correção ao LLM
    e tenta novamente. Se falhar de novo, levanta SchemaValidationError.

    Args:
        raw_response: String JSON retornada pelo LLM.
        llm_client: Client do LLM para chamada de correção.

    Returns:
        AnaliseResultSchema validado.

    Raises:
        SchemaValidationError: Se a validação falhar mesmo após correção.
    """
    result = _try_parse(raw_response)
    if result is not None:
        logger.info("validacao_sucesso", tentativa=1)
        return result

    logger.warning("validacao_falhou", tentativa=1, erro="parse inicial falhou")

    try:
        data = json.loads(raw_response)
        original_json = json.dumps(data, ensure_ascii=False, indent=2)
    except json.JSONDecodeError:
        original_json = raw_response

    try:
        validation_errors = _get_validation_errors(raw_response)
        corrected_response = await llm_client.correct_json(original_json, validation_errors)
    except Exception as exc:
        logger.error("correcao_llm_falhou", erro=str(exc))
        raise SchemaValidationError(f"Falha na correção do LLM: {exc}") from exc

    result = _try_parse(corrected_response)
    if result is not None:
        logger.info("validacao_sucesso", tentativa=2)
        return result

    logger.error("validacao_falhou", tentativa=2, erro="parse após correção falhou")
    raise SchemaValidationError("Resposta do LLM inválida mesmo após correção")


def _try_parse(raw: str) -> AnaliseResultSchema | None:
    """
    Tenta parsear a string JSON no schema Pydantic.

    Args:
        raw: String JSON.

    Returns:
        AnaliseResultSchema ou None se falhar.
    """
    try:
        data = json.loads(raw)
        return AnaliseResultSchema.model_validate(data)
    except (json.JSONDecodeError, ValueError):
        return None


def _get_validation_errors(raw: str) -> str:
    """
    Extrai os erros de validação Pydantic de uma string JSON.

    Args:
        raw: String JSON que falhou na validação.

    Returns:
        Descrição textual dos erros.
    """
    try:
        data = json.loads(raw)
        AnaliseResultSchema.model_validate(data)
        return "Nenhum erro encontrado"
    except json.JSONDecodeError as exc:
        return f"JSON inválido: {exc}"
    except ValueError as exc:
        return str(exc)
