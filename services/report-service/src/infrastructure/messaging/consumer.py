import json
from collections.abc import Callable, Coroutine
from typing import Any

import aio_pika

from src.environment import get_settings
from src.infrastructure.observability.logging import get_logger
from src.infrastructure.observability.tracing import rabbitmq_consume_trace

logger = get_logger()

ROUTING_KEY_ANALISE_CONCLUIDA: str = "analise.processamento.concluida"


class RabbitMQConsumer:
    """Consumer que escuta eventos AnaliseConcluida via RabbitMQ."""

    def __init__(
        self,
        report_handler: Callable[[str, list[dict[str, Any]], list[dict[str, Any]]], Coroutine[Any, Any, None]],
    ) -> None:
        """
        Args:
            report_handler: Async callable que recebe (analise_id, componentes, riscos).
        """
        self._settings = get_settings().rabbitmq
        self._connection: aio_pika.abc.AbstractRobustConnection | None = None
        self._handler = report_handler

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

        await queue.bind(exchange, routing_key=ROUTING_KEY_ANALISE_CONCLUIDA)

        logger.info(
            "rabbitmq_consumer_iniciado",
            queue=self._settings.queue_name,
            routing_key=ROUTING_KEY_ANALISE_CONCLUIDA,
        )

        await queue.consume(self._process_message)

    async def _process_message(self, message: aio_pika.abc.AbstractIncomingMessage) -> None:
        """
        Processa uma mensagem AnaliseConcluida recebida do RabbitMQ.

        Args:
            message: Mensagem recebida da fila.
        """
        async with message.process():
            try:
                with rabbitmq_consume_trace("_process_message", message.headers):
                    body = json.loads(message.body.decode())
                    event_type = body.get("event_type", "")
                    payload = body.get("payload", {})
                    analise_id = payload.get("analise_id")
                    componentes = payload.get("componentes", [])
                    riscos = payload.get("riscos", [])

                    logger.info(
                        "analise_concluida_recebida",
                        event_type=event_type,
                        analise_id=analise_id,
                        total_componentes=len(componentes),
                        total_riscos=len(riscos),
                    )

                    if event_type != "AnaliseConcluida":
                        logger.debug("evento_ignorado", event_type=event_type, analise_id=analise_id)
                        return

                    await self._handler(analise_id, componentes, riscos)

            except Exception:
                logger.exception("erro_processando_evento", message_body=message.body.decode()[:500])

    async def close(self) -> None:
        """Fecha a conexão com o RabbitMQ."""
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
            logger.info("rabbitmq_consumer_desconectado")
