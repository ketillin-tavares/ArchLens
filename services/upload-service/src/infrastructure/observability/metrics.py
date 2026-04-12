import time
from types import ModuleType

from src.infrastructure.observability.logging import get_logger

try:
    import newrelic.agent as _newrelic_agent
except ImportError:
    _newrelic_agent: ModuleType | None = None  # type: ignore[no-redef]

logger = get_logger()


def _record_newrelic_metric(name: str, value: float) -> None:
    """Registra uma métrica customizada no New Relic na transação atual.

    Usa record_custom_metric() no contexto da transação ativa (HTTP ou
    BackgroundTask do RabbitMQ) para gerar timeslice metrics consultáveis
    via metricTimesliceName no NRQL.
    """
    if _newrelic_agent is None:
        return
    _newrelic_agent.record_custom_metric(name, value)


class MetricsRecorder:
    """Registra métricas customizadas de observabilidade no New Relic."""

    @staticmethod
    def record_analise_por_status(status: str) -> None:
        """
        Registra contagem de análises por status.

        Args:
            status: Status da análise (recebido, em_processamento, analisado, erro).
        """
        _record_newrelic_metric(f"Custom/Analise/Status/{status}", 1)
        logger.debug("metrica_analise_status", status=status)

    @staticmethod
    def record_upload_tamanho(tamanho_bytes: int) -> None:
        """
        Registra o tamanho de um arquivo uploaded.

        Args:
            tamanho_bytes: Tamanho do arquivo em bytes.
        """
        _record_newrelic_metric("Custom/Upload/TamanhoBytes", tamanho_bytes)

    @staticmethod
    def record_tempo_processamento(analise_id: str, duracao_segundos: float) -> None:
        """
        Registra o tempo de processamento de uma análise (DiagramaEnviado até RelatorioGerado).

        Args:
            analise_id: ID da análise.
            duracao_segundos: Duração em segundos.
        """
        _record_newrelic_metric("Custom/Analise/TempoProcessamento", duracao_segundos)
        logger.info(
            "metrica_tempo_processamento",
            analise_id=analise_id,
            duracao_segundos=duracao_segundos,
        )

    @staticmethod
    def record_falha() -> None:
        """Registra uma ocorrência de falha (evento AnaliseFalhou)."""
        _record_newrelic_metric("Custom/Analise/Falhas", 1)

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
