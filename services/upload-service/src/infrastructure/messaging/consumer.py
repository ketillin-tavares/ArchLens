import json
from collections.abc import Callable, Coroutine
from typing import Any

import aio_pika
import structlog

from src.environment import get_settings

logger = structlog.get_logger()

EVENT_STATUS_MAP: dict[str, str | None] = {
    "ProcessamentoIniciado": "em_processamento",
    "AnaliseConcluida": None,
    "AnaliseFalhou": "erro",
    "RelatorioGerado": "analisado",
}

ROUTING_KEYS: list[str] = [
    "analise.processamento.iniciado",
    "analise.processamento.concluida",
    "analise.processamento.falhou",
    "analise.relatorio.gerado",
]


class RabbitMQConsumer:
    """Consumer que escuta eventos de status dos outros serviços via RabbitMQ."""

    def __init__(
        self,
        status_update_handler: Callable[[str, str, str | None], Coroutine[Any, Any, None]],
    ) -> None:
        """
        Args:
            status_update_handler: Async callable que recebe (analise_id, novo_status, erro_detalhe).
        """
        self._settings = get_settings().rabbitmq
        self._connection: aio_pika.abc.AbstractRobustConnection | None = None
        self._handler = status_update_handler

    async def start(self) -> None:
        """Conecta ao RabbitMQ, declara exchange/queue, faz binds e inicia consumo."""
        self._connection = await aio_pika.connect_robust(self._settings.url)
        channel = await self._connection.channel()
        await channel.set_qos(prefetch_count=10)

        exchange = await channel.declare_exchange(
            self._settings.exchange_name,
            aio_pika.ExchangeType.TOPIC,
            durable=True,
        )

        queue = await channel.declare_queue(
            self._settings.queue_name,
            durable=True,
        )

        for routing_key in ROUTING_KEYS:
            await queue.bind(exchange, routing_key=routing_key)

        logger.info(
            "rabbitmq_consumer_iniciado",
            queue=self._settings.queue_name,
            routing_keys=ROUTING_KEYS,
        )

        await queue.consume(self._process_message)

    async def _process_message(self, message: aio_pika.abc.AbstractIncomingMessage) -> None:
        """
        Processa uma mensagem recebida do RabbitMQ.

        Args:
            message: Mensagem recebida da fila.
        """
        async with message.process():
            try:
                body = json.loads(message.body.decode())
                event_type = body.get("event_type", "")
                payload = body.get("payload", {})
                analise_id = payload.get("analise_id")

                logger.info("evento_recebido", event_type=event_type, analise_id=analise_id)

                novo_status = EVENT_STATUS_MAP.get(event_type)
                if novo_status is None:
                    logger.debug("evento_ignorado", event_type=event_type, analise_id=analise_id)
                    return

                erro_detalhe = payload.get("erro_detalhe") if event_type == "AnaliseFalhou" else None

                await self._handler(analise_id, novo_status, erro_detalhe)

            except Exception:
                logger.exception("erro_processando_evento", message_body=message.body.decode()[:500])

    async def close(self) -> None:
        """Fecha a conexão com o RabbitMQ."""
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
            logger.info("rabbitmq_consumer_desconectado")
