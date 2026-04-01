import abc


class EventPublisher(abc.ABC):
    """Port (interface) para publicação de eventos no message broker."""

    @abc.abstractmethod
    async def publish_event(self, event_type: str, routing_key: str, payload: dict) -> None:
        """
        Publica um evento no message broker.

        Args:
            event_type: Tipo do evento.
            routing_key: Routing key para roteamento.
            payload: Dados do evento.
        """
