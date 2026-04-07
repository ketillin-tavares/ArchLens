"""Unit tests for messaging infrastructure."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import aio_pika
import pytest

from src.infrastructure.messaging.consumer import RabbitMQConsumer
from src.infrastructure.messaging.publisher import RabbitMQPublisher


class TestRabbitMQPublisher:
    """Tests for the RabbitMQPublisher class."""

    def test_publisher_initialization(self) -> None:
        """Test that RabbitMQPublisher initializes correctly."""
        # Act
        publisher = RabbitMQPublisher()

        # Assert
        assert publisher._connection is None
        assert publisher._channel is None
        assert publisher._exchange is None

    @patch("src.infrastructure.messaging.publisher.aio_pika.connect_robust")
    async def test_connect_establishes_connection(self, mock_connect: AsyncMock) -> None:
        """Test that connect establishes RabbitMQ connection."""
        # Arrange
        mock_connection = AsyncMock()
        mock_channel = AsyncMock()
        mock_exchange = AsyncMock()

        mock_connect.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel
        mock_channel.get_exchange.return_value = mock_exchange

        publisher = RabbitMQPublisher()

        # Act
        await publisher.connect()

        # Assert
        mock_connect.assert_called_once()
        mock_connection.channel.assert_called_once()
        mock_channel.get_exchange.assert_called_once()
        assert publisher._connection == mock_connection
        assert publisher._channel == mock_channel
        assert publisher._exchange == mock_exchange

    @patch("src.infrastructure.messaging.publisher.aio_pika.connect_robust")
    async def test_connect_declares_topic_exchange(self, mock_connect: AsyncMock) -> None:
        """Test that connect retrieves the exchange using the correct name."""
        # Arrange
        mock_connection = AsyncMock()
        mock_channel = AsyncMock()
        mock_exchange = AsyncMock()

        mock_connect.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel
        mock_channel.get_exchange.return_value = mock_exchange

        publisher = RabbitMQPublisher()

        # Act
        await publisher.connect()

        # Assert
        mock_channel.get_exchange.assert_called_once()
        call_args = mock_channel.get_exchange.call_args
        # Verify the exchange name is passed (default is "analise.events" from RabbitMQSettings)
        assert call_args[0][0] == "analise.events"

    async def test_publish_event_raises_if_not_connected(self) -> None:
        """Test that publish_event raises if publisher not connected."""
        # Arrange
        publisher = RabbitMQPublisher()

        # Act & Assert
        with pytest.raises(RuntimeError, match="não conectado"):
            await publisher.publish_event("test_event", "test.routing.key", {"data": "test"})

    @patch("src.infrastructure.messaging.publisher.aio_pika.connect_robust")
    async def test_publish_event_creates_message(self, mock_connect: AsyncMock) -> None:
        """Test that publish_event creates and publishes a message."""
        # Arrange
        mock_connection = AsyncMock()
        mock_channel = AsyncMock()
        mock_exchange = AsyncMock()

        mock_connect.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel
        mock_channel.get_exchange.return_value = mock_exchange

        publisher = RabbitMQPublisher()
        await publisher.connect()

        event_type = "TestEvent"
        routing_key = "test.routing.key"
        payload = {"event_id": "123", "data": "test"}

        # Act
        await publisher.publish_event(event_type, routing_key, payload)

        # Assert
        mock_exchange.publish.assert_called_once()
        call_args = mock_exchange.publish.call_args
        message = call_args[0][0]
        assert call_args[1]["routing_key"] == routing_key

        # Verify message content
        assert isinstance(message, aio_pika.Message)
        assert message.content_type == "application/json"

    @patch("src.infrastructure.messaging.publisher.aio_pika.connect_robust")
    async def test_publish_event_message_body(self, mock_connect: AsyncMock) -> None:
        """Test that published message body contains serialized payload."""
        # Arrange
        mock_connection = AsyncMock()
        mock_channel = AsyncMock()
        mock_exchange = AsyncMock()

        mock_connect.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel
        mock_channel.get_exchange.return_value = mock_exchange

        publisher = RabbitMQPublisher()
        await publisher.connect()

        payload = {"event_type": "TestEvent", "data": "test_data"}

        # Act
        await publisher.publish_event("TestEvent", "test.key", payload)

        # Assert
        call_args = mock_exchange.publish.call_args
        message = call_args[0][0]
        body = message.body.decode()
        parsed = json.loads(body)
        assert parsed == payload

    @patch("src.infrastructure.messaging.publisher.aio_pika.connect_robust")
    async def test_publish_event_persistent_delivery(self, mock_connect: AsyncMock) -> None:
        """Test that published messages use persistent delivery mode."""
        # Arrange
        mock_connection = AsyncMock()
        mock_channel = AsyncMock()
        mock_exchange = AsyncMock()

        mock_connect.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel
        mock_channel.get_exchange.return_value = mock_exchange

        publisher = RabbitMQPublisher()
        await publisher.connect()

        # Act
        await publisher.publish_event("TestEvent", "test.key", {"data": "test"})

        # Assert
        call_args = mock_exchange.publish.call_args
        message = call_args[0][0]
        assert message.delivery_mode == aio_pika.DeliveryMode.PERSISTENT

    @patch("src.infrastructure.messaging.publisher.aio_pika.connect_robust")
    async def test_close_closes_connection(self, mock_connect: AsyncMock) -> None:
        """Test that close closes the RabbitMQ connection."""
        # Arrange
        mock_connection = AsyncMock()
        mock_channel = AsyncMock()
        mock_exchange = AsyncMock()
        mock_connection.is_closed = False

        mock_connect.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel
        mock_channel.get_exchange.return_value = mock_exchange

        publisher = RabbitMQPublisher()
        await publisher.connect()

        # Act
        await publisher.close()

        # Assert
        mock_connection.close.assert_called_once()

    async def test_close_handles_already_closed(self) -> None:
        """Test that close handles already closed connection."""
        # Arrange
        publisher = RabbitMQPublisher()

        # Act & Assert - should not raise
        await publisher.close()

    @patch("src.infrastructure.messaging.publisher.aio_pika.connect_robust")
    async def test_multiple_publish_events(self, mock_connect: AsyncMock) -> None:
        """Test publishing multiple events in sequence."""
        # Arrange
        mock_connection = AsyncMock()
        mock_channel = AsyncMock()
        mock_exchange = AsyncMock()

        mock_connect.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel
        mock_channel.get_exchange.return_value = mock_exchange

        publisher = RabbitMQPublisher()
        await publisher.connect()

        # Act
        await publisher.publish_event("Event1", "routing.1", {"id": 1})
        await publisher.publish_event("Event2", "routing.2", {"id": 2})
        await publisher.publish_event("Event3", "routing.3", {"id": 3})

        # Assert
        assert mock_exchange.publish.call_count == 3


@patch("src.infrastructure.observability.tracing._newrelic_agent", None)
class TestRabbitMQConsumer:
    """Tests for the RabbitMQConsumer class."""

    def test_consumer_initialization(self) -> None:
        """Test that RabbitMQConsumer initializes correctly."""
        # Arrange
        mock_handler = AsyncMock()

        # Act
        consumer = RabbitMQConsumer(report_handler=mock_handler)

        # Assert
        assert consumer._handler == mock_handler
        assert consumer._connection is None

    @patch("src.infrastructure.messaging.consumer.aio_pika.connect_robust")
    async def test_start_connects_and_binds(self, mock_connect: AsyncMock) -> None:
        """Test that start connects, configures QoS, gets exchange, declares queue, binds and consumes."""
        # Arrange
        mock_handler = AsyncMock()
        mock_connection = AsyncMock()
        mock_channel = AsyncMock()
        mock_exchange = AsyncMock()
        mock_queue = AsyncMock()

        mock_connect.return_value = mock_connection
        mock_connection.channel = AsyncMock(return_value=mock_channel)
        mock_channel.set_qos = AsyncMock()
        mock_channel.get_exchange = AsyncMock(return_value=mock_exchange)
        mock_channel.declare_queue = AsyncMock(return_value=mock_queue)
        mock_queue.bind = AsyncMock()
        mock_queue.consume = AsyncMock()

        consumer = RabbitMQConsumer(report_handler=mock_handler)

        # Act
        await consumer.start()

        # Assert
        mock_connect.assert_called_once()
        mock_connection.channel.assert_called_once()
        mock_channel.set_qos.assert_called_once_with(prefetch_count=10)
        mock_channel.get_exchange.assert_called_once()
        mock_channel.declare_queue.assert_called_once()
        mock_queue.bind.assert_called_once()
        mock_queue.consume.assert_called_once_with(consumer._process_message)

    async def test_process_message_ignores_non_analise_concluida_event(self) -> None:
        """Test that consumer ignores events that are not AnaliseConcluida."""
        # Arrange
        mock_handler = AsyncMock()
        consumer = RabbitMQConsumer(report_handler=mock_handler)

        event_body = {
            "event_type": "OutroEvento",
            "payload": {
                "analise_id": "123",
                "componentes": [],
                "riscos": [],
            },
        }

        mock_message = AsyncMock(spec=aio_pika.abc.AbstractIncomingMessage)
        mock_message.body = json.dumps(event_body).encode()
        mock_message.process = MagicMock(return_value=AsyncMock())
        mock_message.process.return_value.__aenter__ = AsyncMock()
        mock_message.process.return_value.__aexit__ = AsyncMock()

        # Act
        await consumer._process_message(mock_message)

        # Assert - handler should not be called
        mock_handler.assert_not_called()

    async def test_process_message_handles_malformed_json(self) -> None:
        """Test that consumer handles malformed JSON gracefully."""
        # Arrange
        mock_handler = AsyncMock()
        consumer = RabbitMQConsumer(report_handler=mock_handler)

        mock_message = AsyncMock(spec=aio_pika.abc.AbstractIncomingMessage)
        mock_message.body = b"invalid json {{"
        mock_message.process = MagicMock(return_value=AsyncMock())
        mock_message.process.return_value.__aenter__ = AsyncMock()
        mock_message.process.return_value.__aexit__ = AsyncMock()

        # Act & Assert - should not raise
        await consumer._process_message(mock_message)

        # Assert - handler should not be called
        mock_handler.assert_not_called()

    async def test_process_message_calls_handler_for_valid_analise_concluida(self) -> None:
        """Test that consumer calls handler for valid AnaliseConcluida events."""
        # Arrange
        mock_handler = AsyncMock()
        consumer = RabbitMQConsumer(report_handler=mock_handler)

        event_body = {
            "event_type": "AnaliseConcluida",
            "payload": {
                "analise_id": "test-123",
                "componentes": [{"id": "comp1", "nome": "Componente 1"}],
                "riscos": [{"id": "risk1", "nivel": "alta"}],
            },
        }

        mock_message = AsyncMock(spec=aio_pika.abc.AbstractIncomingMessage)
        mock_message.body = json.dumps(event_body).encode()
        mock_message.headers = {}
        mock_message.process = MagicMock(return_value=AsyncMock())
        mock_message.process.return_value.__aenter__ = AsyncMock()
        mock_message.process.return_value.__aexit__ = AsyncMock()

        # Act
        await consumer._process_message(mock_message)

        # Assert
        mock_handler.assert_called_once_with(
            "test-123",
            [{"id": "comp1", "nome": "Componente 1"}],
            [{"id": "risk1", "nivel": "alta"}],
        )

    async def test_process_message_with_missing_payload_fields(self) -> None:
        """Test that consumer handles missing payload fields gracefully."""
        # Arrange
        mock_handler = AsyncMock()
        consumer = RabbitMQConsumer(report_handler=mock_handler)

        event_body = {
            "event_type": "AnaliseConcluida",
            "payload": {
                "analise_id": "test-123",
                # componentes and riscos are missing
            },
        }

        mock_message = AsyncMock(spec=aio_pika.abc.AbstractIncomingMessage)
        mock_message.body = json.dumps(event_body).encode()
        mock_message.headers = {}
        mock_message.process = MagicMock(return_value=AsyncMock())
        mock_message.process.return_value.__aenter__ = AsyncMock()
        mock_message.process.return_value.__aexit__ = AsyncMock()

        # Act
        await consumer._process_message(mock_message)

        # Assert - handler should be called with empty lists for missing fields
        mock_handler.assert_called_once_with("test-123", [], [])

    async def test_process_message_empty_payload(self) -> None:
        """Test that consumer handles empty payload."""
        # Arrange
        mock_handler = AsyncMock()
        consumer = RabbitMQConsumer(report_handler=mock_handler)

        event_body = {
            "event_type": "AnaliseConcluida",
            "payload": {},
        }

        mock_message = AsyncMock(spec=aio_pika.abc.AbstractIncomingMessage)
        mock_message.body = json.dumps(event_body).encode()
        mock_message.headers = {}
        mock_message.process = MagicMock(return_value=AsyncMock())
        mock_message.process.return_value.__aenter__ = AsyncMock()
        mock_message.process.return_value.__aexit__ = AsyncMock()

        # Act
        await consumer._process_message(mock_message)

        # Assert
        mock_handler.assert_called_once_with(None, [], [])

    async def test_close_with_active_connection(self) -> None:
        """Test closing consumer with an active connection."""
        # Arrange
        mock_handler = AsyncMock()
        consumer = RabbitMQConsumer(report_handler=mock_handler)
        mock_connection = AsyncMock()
        mock_connection.is_closed = False
        consumer._connection = mock_connection

        # Act
        await consumer.close()

        # Assert
        mock_connection.close.assert_called_once()

    async def test_close_without_connection(self) -> None:
        """Test closing consumer without a connection."""
        # Arrange
        mock_handler = AsyncMock()
        consumer = RabbitMQConsumer(report_handler=mock_handler)

        # Act & Assert — should not raise
        await consumer.close()


class TestRabbitMQConsumerNewRelic:
    """Tests for consumer with New Relic integration."""

    @pytest.mark.asyncio
    @patch("src.infrastructure.observability.tracing._newrelic_agent")
    async def test_process_message_with_newrelic_tracing(self, mock_nr_agent: MagicMock) -> None:
        """Test that _process_message calls New Relic tracing when agent is available."""
        # Arrange
        mock_handler = AsyncMock()
        consumer = RabbitMQConsumer(report_handler=mock_handler)

        event_body = {
            "event_type": "AnaliseConcluida",
            "payload": {
                "analise_id": "test-123",
                "componentes": [{"id": "c1"}],
                "riscos": [],
            },
        }

        mock_message = AsyncMock(spec=aio_pika.abc.AbstractIncomingMessage)
        mock_message.body = json.dumps(event_body).encode()
        mock_message.headers = {"traceparent": "00-abc-def-01"}
        mock_message.process = MagicMock(return_value=AsyncMock())
        mock_message.process.return_value.__aenter__ = AsyncMock()
        mock_message.process.return_value.__aexit__ = AsyncMock()

        # Act
        await consumer._process_message(mock_message)

        # Assert
        mock_nr_agent.accept_distributed_trace_headers.assert_called_once_with(
            {"traceparent": "00-abc-def-01"}, transport_type="AMQP"
        )
        mock_handler.assert_called_once()
