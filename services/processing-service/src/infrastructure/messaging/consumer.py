import json
from collections.abc import Callable, Coroutine
from types import ModuleType
from typing import Any

import aio_pika
import structlog

from src.environment import get_settings

try:
    import newrelic.agent as _newrelic_agent
except ImportError:
    _newrelic_agent: ModuleType | None = None  # type: ignore[no-redef]

logger = structlog.get_logger()

ROUTING_KEY_DIAGRAMA_ENVIADO: str = "analise.diagrama.enviado"


class RabbitMQConsumer:
    """Consumer que escuta eventos DiagramaEnviado via RabbitMQ."""

    def __init__(
        self,
        diagram_handler: Callable[[str, str, str], Coroutine[Any, Any, None]],
    ) -> None:
        """
        Args:
            diagram_handler: Async callable que recebe (analise_id, diagrama_storage_path, content_type).
        """
        self._settings = get_settings().rabbitmq
        self._connection: aio_pika.abc.AbstractRobustConnection | None = None
        self._handler = diagram_handler

    async def start(self) -> None:
        """Conecta ao RabbitMQ, declara exchange/queue, faz bind e inicia consumo."""
        self._connection = await aio_pika.connect_robust(self._settings.url)
        channel = await self._connection.channel()
        await channel.set_qos(prefetch_count=10)

        exchange = await channel.get_exchange(
            self._settings.exchange_name,
        )

        queue = await channel.declare_queue(
            self._settings.queue_name,
            passive=True,
        )

        await queue.bind(exchange, routing_key=ROUTING_KEY_DIAGRAMA_ENVIADO)

        logger.info(
            "rabbitmq_consumer_iniciado",
            queue=self._settings.queue_name,
            routing_key=ROUTING_KEY_DIAGRAMA_ENVIADO,
        )

        await queue.consume(self._process_message)

    async def _process_message(self, message: aio_pika.abc.AbstractIncomingMessage) -> None:
        """
        Processa uma mensagem DiagramaEnviado recebida do RabbitMQ.

        Args:
            message: Mensagem recebida da fila.
        """
        async with message.process():
            try:
                if _newrelic_agent is not None:
                    trace_headers = message.headers if isinstance(message.headers, dict) else {}
                    _newrelic_agent.accept_distributed_trace_headers(trace_headers, transport_type="AMQP")

                body = json.loads(message.body.decode())
                event_type = body.get("event_type", "")
                payload = body.get("payload", {})
                analise_id = payload.get("analise_id")
                diagrama_storage_path = payload.get("diagrama_storage_path")
                content_type = payload.get("content_type")

                logger.info(
                    "diagrama_enviado_recebido",
                    event_type=event_type,
                    analise_id=analise_id,
                )

                if event_type != "DiagramaEnviado":
                    logger.debug("evento_ignorado", event_type=event_type, analise_id=analise_id)
                    return

                await self._handler(analise_id, diagrama_storage_path, content_type)

            except Exception:
                logger.exception("erro_processando_evento", message_body=message.body.decode()[:500])

    async def close(self) -> None:
        """Fecha a conexão com o RabbitMQ."""
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
            logger.info("rabbitmq_consumer_desconectado")
