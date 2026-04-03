import structlog

from src.domain.exceptions import AnaliseInsanaError
from src.domain.schemas import AnaliseResultSchema

logger = structlog.get_logger()

MAX_COMPONENTES: int = 30
MAX_RISCOS: int = 20
MIN_CONFIANCA_MEDIA: float = 0.4


def check_sanity(result: AnaliseResultSchema) -> None:
    """
    Aplica limites anti-alucinação na resposta do LLM.

    Args:
        result: Schema validado da resposta da IA.

    Raises:
        AnaliseInsanaError: Se algum limite for violado.
    """
    total_componentes = len(result.componentes)
    total_riscos = len(result.riscos)

    if total_componentes > MAX_COMPONENTES:
        logger.error(
            "sanity_check_falhou",
            motivo="excesso_componentes",
            total=total_componentes,
            limite=MAX_COMPONENTES,
        )
        raise AnaliseInsanaError(f"Número excessivo de componentes: {total_componentes} (máximo: {MAX_COMPONENTES})")

    if total_riscos > MAX_RISCOS:
        logger.error(
            "sanity_check_falhou",
            motivo="excesso_riscos",
            total=total_riscos,
            limite=MAX_RISCOS,
        )
        raise AnaliseInsanaError(f"Número excessivo de riscos: {total_riscos} (máximo: {MAX_RISCOS})")

    if total_componentes > 0:
        media_confianca = sum(c.confianca for c in result.componentes) / total_componentes
        if media_confianca < MIN_CONFIANCA_MEDIA:
            logger.error(
                "sanity_check_falhou",
                motivo="confianca_baixa",
                media=media_confianca,
                limite=MIN_CONFIANCA_MEDIA,
            )
            raise AnaliseInsanaError(
                f"Confiança média muito baixa: {media_confianca:.2f} (mínimo: {MIN_CONFIANCA_MEDIA})"
            )

    logger.info("sanity_check_ok", total_componentes=total_componentes, total_riscos=total_riscos)
