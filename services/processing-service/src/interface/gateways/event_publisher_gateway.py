from src.application.ports import EventPublisher
from src.infrastructure.messaging.publisher import RabbitMQPublisher


class RabbitMQEventPublisherGateway(EventPublisher):
    """Adapter que implementa EventPublisher usando RabbitMQ."""

    def __init__(self, publisher: RabbitMQPublisher | None = None) -> None:
        self._publisher = publisher

    def set_publisher(self, publisher: RabbitMQPublisher) -> None:
        """
        Define a instância do publisher RabbitMQ.

        Args:
            publisher: Instância conectada do RabbitMQPublisher.
        """
        self._publisher = publisher

    async def publish_event(self, event_type: str, routing_key: str, payload: dict) -> None:
        """
        Publica um evento no RabbitMQ via publisher.

        Args:
            event_type: Tipo do evento.
            routing_key: Routing key para roteamento.
            payload: Dados do evento.
        """
        if self._publisher is None:
            raise RuntimeError("Publisher RabbitMQ não configurado. Use set_publisher() ou passe no construtor.")

        await self._publisher.publish_event(event_type, routing_key, payload)
