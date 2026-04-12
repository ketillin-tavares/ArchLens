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


def _record_newrelic_event(event_type: str, params: dict) -> None:
    """Registra um evento customizado no New Relic na transação atual.

    Usa record_custom_event() no contexto da transação ativa para gerar
    custom events consultáveis via FROM EventType no NRQL.
    """
    if _newrelic_agent is None:
        return
    _newrelic_agent.record_custom_event(event_type, params)


class MetricsRecorder:
    """Registra métricas customizadas de observabilidade no New Relic."""

    @staticmethod
    def record_component_count(count: int) -> None:
        """Registra contagem de componentes por análise."""
        _record_newrelic_metric("Custom/AI/ComponentCount", count)

    @staticmethod
    def record_risk_count(count: int) -> None:
        """Registra contagem de riscos por análise."""
        _record_newrelic_metric("Custom/AI/RiskCount", count)

    @staticmethod
    def record_avg_confidence(avg: float) -> None:
        """Registra confiança média dos componentes."""
        _record_newrelic_metric("Custom/AI/AvgConfidence", avg)

    @staticmethod
    def record_latency(duracao_segundos: float) -> None:
        """Registra duração do pipeline em segundos."""
        _record_newrelic_metric("Custom/AI/LatencySeconds", duracao_segundos)

    @staticmethod
    def record_validation_retries(count: int) -> None:
        """Registra quantas vezes a validação precisou de correção."""
        _record_newrelic_metric("Custom/AI/ValidationRetries", count)

    @staticmethod
    def record_analise_iniciada(analise_id: str) -> None:
        """Registra evento de análise iniciada."""
        _record_newrelic_event("AnaliseIniciada", {"analise_id": analise_id})

    @staticmethod
    def record_analise_sucesso(
        analise_id: str, duracao_segundos: float, total_componentes: int, total_riscos: int
    ) -> None:
        """Registra evento de análise concluída com sucesso."""
        _record_newrelic_event(
            "AnaliseSucesso",
            {
                "analise_id": analise_id,
                "duracao_segundos": duracao_segundos,
                "total_componentes": total_componentes,
                "total_riscos": total_riscos,
            },
        )

    @staticmethod
    def record_analise_falha(analise_id: str, erro: str, tipo_erro: str) -> None:
        """Registra evento de análise falhou."""
        _record_newrelic_event(
            "AnaliseFalha",
            {"analise_id": analise_id, "erro": erro, "tipo_erro": tipo_erro},
        )

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
