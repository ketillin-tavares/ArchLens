import json
from types import ModuleType

import aio_pika

from src.environment import get_settings
from src.infrastructure.observability.logging import get_logger

try:
    import newrelic.agent as _newrelic_agent
except ImportError:
    _newrelic_agent: ModuleType | None = None  # type: ignore[no-redef]

logger = get_logger()


class RabbitMQPublisher:
    """Publisher para enviar eventos ao RabbitMQ via topic exchange."""

    def __init__(self) -> None:
        self._settings = get_settings().rabbitmq
        self._connection: aio_pika.abc.AbstractRobustConnection | None = None
        self._channel: aio_pika.abc.AbstractChannel | None = None
        self._exchange: aio_pika.abc.AbstractExchange | None = None

    async def connect(self) -> None:
        """Estabelece conexão com o RabbitMQ e declara o exchange."""
        self._connection = await aio_pika.connect_robust(self._settings.url)
        self._channel = await self._connection.channel()
        self._exchange = await self._channel.get_exchange(
            self._settings.exchange_name,
        )
        logger.info("rabbitmq_publisher_conectado", exchange=self._settings.exchange_name)

    async def publish_event(self, event_type: str, routing_key: str, payload: dict) -> None:
        """
        Publica um evento no exchange RabbitMQ.

        Args:
            event_type: Tipo do evento (ex: DiagramaEnviado).
            routing_key: Routing key do evento (ex: analise.diagrama.enviado).
            payload: Dados do evento serializados como dicionário.
        """
        if not self._exchange:
            raise RuntimeError("Publisher não conectado. Chame connect() primeiro.")

        message_body = json.dumps(payload).encode()

        headers: dict = {}
        if _newrelic_agent is not None:
            nr_headers = []
            _newrelic_agent.insert_distributed_trace_headers(nr_headers)
            headers.update(dict(nr_headers))

        message = aio_pika.Message(
            body=message_body,
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            headers=headers or None,
        )

        await self._exchange.publish(message, routing_key=routing_key)
        logger.info("evento_publicado", event_type=event_type, routing_key=routing_key)

    async def close(self) -> None:
        """Fecha a conexão com o RabbitMQ."""
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
            logger.info("rabbitmq_publisher_desconectado")
