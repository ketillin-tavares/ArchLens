import logging as _stdlib_logging
import sys
from types import ModuleType
from typing import Any

from loguru import logger

try:
    import newrelic.agent as _newrelic_agent
except ImportError:
    _newrelic_agent: ModuleType | None = None  # type: ignore[no-redef]

_ERROR_LEVELS = frozenset({"ERROR", "CRITICAL"})


def _terminal_formatter(record: dict[str, Any]) -> str:
    """
    Formata logs para exibicao legivel no terminal com campos extras.

    Args:
        record: Dicionario com dados do log record do loguru.

    Returns:
        String de formato para o loguru renderizar.
    """
    extra = record["extra"]
    extra_str = ""
    if extra:
        parts = " ".join(f"<cyan>{k}</cyan>=<yellow>{v}</yellow>" for k, v in extra.items())
        extra_str = f" | {parts}"

    base = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
        f"{extra_str}"
        "\n"
    )

    if record["exception"]:
        base += "{exception}"

    return base


class _StdlibLogSink:
    """
    Sink que roteia logs do loguru para o stdlib logging.

    O agente New Relic intercepta o stdlib logging e encaminha os logs
    para a plataforma NR Logs com metadados estruturados, incluindo
    o campo 'message' que o structlog nao fornecia.
    """

    def __init__(self, log_level: str) -> None:
        """
        Inicializa o sink com um logger stdlib configurado.

        Args:
            log_level: Nivel de log (DEBUG, INFO, WARNING, ERROR).
        """
        self._stdlib_logger = _stdlib_logging.getLogger("archlens")
        stdlib_level = getattr(_stdlib_logging, log_level.upper(), _stdlib_logging.INFO)
        self._stdlib_logger.setLevel(stdlib_level)

        if not self._stdlib_logger.handlers:
            self._stdlib_logger.addHandler(_stdlib_logging.NullHandler())

    def write(self, message: Any) -> None:
        """
        Encaminha log record do loguru para stdlib logging com campos extras.

        Args:
            message: Objeto Message do loguru contendo o record completo.
        """
        record = message.record

        log_record = _stdlib_logging.LogRecord(
            name="archlens",
            level=record["level"].no,
            pathname=str(record["file"].path) if record["file"] else "",
            lineno=record["line"],
            msg=record["message"],
            args=(),
            exc_info=None,
        )

        for key, value in record["extra"].items():
            setattr(log_record, key, value)

        self._stdlib_logger.handle(log_record)

        if _newrelic_agent is not None and record["level"].name in _ERROR_LEVELS:
            exc = record["exception"]
            if exc and exc.value:
                _newrelic_agent.notice_error(error=(exc.type, exc.value, exc.traceback))
            else:
                _newrelic_agent.notice_error()


def configure_logging(log_level: str = "INFO") -> None:
    """
    Configura o loguru com dois sinks: terminal legivel e New Relic estruturado.

    Sink 1 (stdout): formato colorido e legivel para desenvolvedores.
    Sink 2 (stdlib): roteia para logging padrao do Python, permitindo que o
    agente New Relic intercepte e encaminhe para NR Logs com o campo 'message'.

    Args:
        log_level: Nivel de log (DEBUG, INFO, WARNING, ERROR).
    """
    logger.remove()

    logger.add(  # type: ignore
        sys.stdout,
        level=log_level.upper(),
        format=_terminal_formatter,
        colorize=True,
    )

    stdlib_sink = _StdlibLogSink(log_level)
    logger.add(
        stdlib_sink.write,
        level=log_level.upper(),
        format="{message}",
    )


class _StructuredLogger:
    """
    Adapter que aceita keyword arguments no estilo structlog.

    Permite manter a mesma API de chamada em todo o codigo:
        logger.info("evento", chave=valor)

    Internamente delega para o loguru com bind() para dados estruturados.
    """

    def debug(self, msg: str, **kwargs: Any) -> None:
        """Loga mensagem no nivel DEBUG com campos estruturados."""
        logger.opt(depth=1).bind(**kwargs).debug(msg)

    def info(self, msg: str, **kwargs: Any) -> None:
        """Loga mensagem no nivel INFO com campos estruturados."""
        logger.opt(depth=1).bind(**kwargs).info(msg)

    def warning(self, msg: str, **kwargs: Any) -> None:
        """Loga mensagem no nivel WARNING com campos estruturados."""
        logger.opt(depth=1).bind(**kwargs).warning(msg)

    def error(self, msg: str, **kwargs: Any) -> None:
        """Loga mensagem no nivel ERROR com campos estruturados."""
        logger.opt(depth=1).bind(**kwargs).error(msg)

    def exception(self, msg: str, **kwargs: Any) -> None:
        """Loga mensagem no nivel ERROR com traceback da excecao atual."""
        logger.opt(depth=1, exception=True).bind(**kwargs).error(msg)

    def critical(self, msg: str, **kwargs: Any) -> None:
        """Loga mensagem no nivel CRITICAL com campos estruturados."""
        logger.opt(depth=1).bind(**kwargs).critical(msg)


_logger_instance = _StructuredLogger()


def get_logger() -> _StructuredLogger:
    """
    Retorna uma instancia do logger estruturado.

    Uso:
        from src.infrastructure.observability.logging import get_logger
        logger = get_logger()
        logger.info("evento", chave="valor")

    Returns:
        Instancia singleton de _StructuredLogger.
    """
    return _logger_instance
