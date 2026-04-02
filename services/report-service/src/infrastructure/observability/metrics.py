import time
from types import ModuleType

import structlog

try:
    import newrelic.agent as _newrelic_agent
except ImportError:
    _newrelic_agent: ModuleType | None = None  # type: ignore[no-redef]

logger = structlog.get_logger()


def _record_newrelic_metric(name: str, value: float) -> None:
    """Registra uma métrica customizada no New Relic, se disponível."""
    if _newrelic_agent is not None:
        _newrelic_agent.record_custom_metric(name, value)


class MetricsRecorder:
    """Registra métricas customizadas de observabilidade no New Relic."""

    @staticmethod
    def record_relatorio_gerado() -> None:
        """Registra contagem de relatórios gerados."""
        _record_newrelic_metric("Custom/Relatorio/Gerados", 1)
        logger.debug("metrica_relatorio_gerado")

    @staticmethod
    def record_tempo_geracao(analise_id: str, duracao_segundos: float) -> None:
        """
        Registra o tempo de geração de um relatório.

        Args:
            analise_id: ID da análise.
            duracao_segundos: Duração em segundos.
        """
        _record_newrelic_metric("Custom/Relatorio/TempoGeracao", duracao_segundos)
        logger.info(
            "metrica_tempo_geracao",
            analise_id=analise_id,
            duracao_segundos=duracao_segundos,
        )

    @staticmethod
    def record_relatorio_duplicado() -> None:
        """Registra contagem de relatórios duplicados ignorados."""
        _record_newrelic_metric("Custom/Relatorio/Duplicados", 1)

    @staticmethod
    def record_relatorio_consultado() -> None:
        """Registra contagem de consultas a relatórios."""
        _record_newrelic_metric("Custom/Relatorio/Consultas", 1)

    @staticmethod
    def start_timer() -> float:
        """
        Inicia um timer para medir duração.

        Returns:
            Timestamp de início.
        """
        return time.monotonic()

    @staticmethod
    def elapsed(start: float) -> float:
        """
        Calcula o tempo decorrido desde o start.

        Args:
            start: Timestamp de início retornado por start_timer().

        Returns:
            Duração em segundos.
        """
        return time.monotonic() - start
