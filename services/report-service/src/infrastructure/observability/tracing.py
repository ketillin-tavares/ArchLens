from collections.abc import Generator
from contextlib import contextmanager
from types import ModuleType

try:
    import newrelic.agent as _newrelic_agent
except ImportError:
    _newrelic_agent: ModuleType | None = None  # type: ignore[no-redef]


@contextmanager
def rabbitmq_consume_trace(name: str, headers: dict) -> Generator[None]:
    """
    Context manager que envolve o processamento de uma mensagem RabbitMQ
    em uma transação background do New Relic, habilitando o distributed tracing.

    Quando o agente New Relic não está disponível, atua como no-op.

    Args:
        name: Nome da transação exibida no New Relic (ex: nome do método handler).
        headers: Headers da mensagem AMQP contendo os dados de trace distribuído.

    Yields:
        None
    """
    if _newrelic_agent is None:
        yield
        return

    with _newrelic_agent.BackgroundTask(_newrelic_agent.application(), name=name, group="RabbitMQ"):
        _newrelic_agent.accept_distributed_trace_headers(
            headers if isinstance(headers, dict) else {},
            transport_type="AMQP",
        )
        yield
