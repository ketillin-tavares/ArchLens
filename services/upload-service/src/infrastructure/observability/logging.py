import logging
import sys
from collections.abc import Mapping, MutableMapping
from types import ModuleType
from typing import Any

import structlog

try:
    import newrelic.agent as _newrelic_agent
except ImportError:
    _newrelic_agent: ModuleType | None = None  # type: ignore[no-redef]


def configure_logging(log_level: str = "INFO") -> None:
    """
    Configura o structlog para output em formato JSON com integração New Relic.

    Args:
        log_level: Nível de log (DEBUG, INFO, WARNING, ERROR).
    """
    processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    if _newrelic_agent is not None:
        processors.append(_newrelic_linking_metadata)

    processors.append(structlog.processors.JSONRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(logging.getLevelName(log_level)),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )


def _newrelic_linking_metadata(
    logger: Any, method_name: str, event_dict: MutableMapping[str, Any]
) -> Mapping[str, Any]:
    """Injeta trace context do New Relic nos logs para linking."""
    if _newrelic_agent is None:
        return event_dict

    metadata = _newrelic_agent.get_linking_metadata()
    if metadata:
        event_dict["nr.entityName"] = metadata.get("entity.name", "")
        event_dict["nr.entityGuid"] = metadata.get("entity.guid", "")
        trace_id = metadata.get("trace.id", "")
        span_id = metadata.get("span.id", "")
        if trace_id:
            event_dict["trace.id"] = trace_id
        if span_id:
            event_dict["span.id"] = span_id
    return event_dict
