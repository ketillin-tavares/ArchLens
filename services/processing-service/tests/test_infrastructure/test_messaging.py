"""Unit tests for messaging infrastructure."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.infrastructure.messaging.consumer import RabbitMQConsumer
from src.infrastructure.messaging.publisher import RabbitMQPublisher


class TestRabbitMQPublisher:
    """Tests for RabbitMQPublisher."""

    @patch("src.infrastructure.messaging.publisher.get_settings")
    def test_publisher_initialization(self, mock_get_settings) -> None:
        """Test publisher initializes correctly."""
        # Arrange
        mock_settings = MagicMock()
        mock_settings.rabbitmq.url = "amqp://guest:guest@localhost/"
        mock_settings.rabbitmq.exchange_name = "archlens"
        mock_get_settings.return_value = mock_settings

        # Act
        publisher = RabbitMQPublisher()

        # Assert
        assert publisher is not None
        assert publisher._connection is None
        assert publisher._channel is None
        assert publisher._exchange is None

    @pytest.mark.asyncio
    @patch("src.infrastructure.messaging.publisher.aio_pika.connect_robust")
    @patch("src.infrastructure.messaging.publisher.get_settings")
    async def test_publisher_connect(self, mock_get_settings, mock_connect) -> None:
        """Test publisher connect establishes connection."""
        # Arrange
        mock_settings = MagicMock()
        mock_settings.rabbitmq.url = "amqp://guest:guest@localhost/"
        mock_settings.rabbitmq.exchange_name = "archlens"
        mock_get_settings.return_value = mock_settings

        mock_connection = AsyncMock()
        mock_channel = AsyncMock()
        mock_exchange = AsyncMock()
        mock_connection.channel.return_value = mock_channel
        mock_channel.declare_exchange.return_value = mock_exchange
        mock_connect.return_value = mock_connection

        publisher = RabbitMQPublisher()

        # Act
        await publisher.connect()

        # Assert
        assert publisher._connection == mock_connection
        assert publisher._channel == mock_channel
        assert publisher._exchange == mock_exchange
        mock_connect.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.infrastructure.messaging.publisher.aio_pika.connect_robust")
    @patch("src.infrastructure.messaging.publisher.get_settings")
    async def test_publish_event_success(self, mock_get_settings, mock_connect) -> None:
        """Test publish_event successfully publishes an event."""
        # Arrange
        mock_settings = MagicMock()
        mock_settings.rabbitmq.url = "amqp://guest:guest@localhost/"
        mock_settings.rabbitmq.exchange_name = "archlens"
        mock_get_settings.return_value = mock_settings

        mock_connection = AsyncMock()
        mock_channel = AsyncMock()
        mock_exchange = AsyncMock()
        mock_connection.channel.return_value = mock_channel
        mock_channel.declare_exchange.return_value = mock_exchange
        mock_connect.return_value = mock_connection

        publisher = RabbitMQPublisher()
        await publisher.connect()

        # Act
        await publisher.publish_event("TestEvent", "test.routing.key", {"data": "test"})

        # Assert
        mock_exchange.publish.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.infrastructure.messaging.publisher.get_settings")
    async def test_publish_event_without_connection(self, mock_get_settings) -> None:
        """Test publish_event raises error without connection."""
        # Arrange
        mock_settings = MagicMock()
        mock_settings.rabbitmq.url = "amqp://guest:guest@localhost/"
        mock_settings.rabbitmq.exchange_name = "archlens"
        mock_get_settings.return_value = mock_settings

        publisher = RabbitMQPublisher()
        publisher._exchange = None

        # Act & Assert
        with pytest.raises(RuntimeError, match="Publisher não conectado"):
            await publisher.publish_event("TestEvent", "test.key", {})

    @pytest.mark.asyncio
    @patch("src.infrastructure.messaging.publisher.aio_pika.connect_robust")
    @patch("src.infrastructure.messaging.publisher.get_settings")
    async def test_publisher_close(self, mock_get_settings, mock_connect) -> None:
        """Test publisher close disconnects from RabbitMQ."""
        # Arrange
        mock_settings = MagicMock()
        mock_settings.rabbitmq.url = "amqp://guest:guest@localhost/"
        mock_settings.rabbitmq.exchange_name = "archlens"
        mock_get_settings.return_value = mock_settings

        mock_connection = AsyncMock()
        mock_connection.is_closed = False
        mock_channel = AsyncMock()
        mock_exchange = AsyncMock()
        mock_connection.channel.return_value = mock_channel
        mock_channel.declare_exchange.return_value = mock_exchange
        mock_connect.return_value = mock_connection

        publisher = RabbitMQPublisher()
        await publisher.connect()

        # Act
        await publisher.close()

        # Assert
        mock_connection.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.infrastructure.messaging.publisher.get_settings")
    async def test_publisher_close_already_closed(self, mock_get_settings) -> None:
        """Test publisher close handles already closed connection."""
        # Arrange
        mock_settings = MagicMock()
        mock_settings.rabbitmq.url = "amqp://guest:guest@localhost/"
        mock_settings.rabbitmq.exchange_name = "archlens"
        mock_get_settings.return_value = mock_settings

        publisher = RabbitMQPublisher()
        publisher._connection = None

        # Act
        await publisher.close()

        # Assert - Should not raise


class TestRabbitMQConsumer:
    """Tests for RabbitMQConsumer."""

    @patch("src.infrastructure.messaging.consumer.get_settings")
    def test_consumer_initialization(self, mock_get_settings) -> None:
        """Test consumer initializes correctly."""
        # Arrange
        mock_settings = MagicMock()
        mock_settings.rabbitmq.url = "amqp://guest:guest@localhost/"
        mock_settings.rabbitmq.exchange_name = "archlens"
        mock_settings.rabbitmq.queue_name = "processing-queue"
        mock_get_settings.return_value = mock_settings

        mock_handler = AsyncMock()

        # Act
        consumer = RabbitMQConsumer(diagram_handler=mock_handler)

        # Assert
        assert consumer is not None
        assert consumer._handler == mock_handler
        assert consumer._connection is None

    @pytest.mark.asyncio
    @patch("src.infrastructure.messaging.consumer.aio_pika.connect_robust")
    @patch("src.infrastructure.messaging.consumer.get_settings")
    async def test_consumer_start(self, mock_get_settings, mock_connect) -> None:
        """Test consumer start establishes connection."""
        # Arrange
        mock_settings = MagicMock()
        mock_settings.rabbitmq.url = "amqp://guest:guest@localhost/"
        mock_settings.rabbitmq.exchange_name = "archlens"
        mock_settings.rabbitmq.queue_name = "processing-queue"
        mock_get_settings.return_value = mock_settings

        mock_connection = AsyncMock()
        mock_channel = AsyncMock()
        mock_exchange = AsyncMock()
        mock_queue = AsyncMock()
        mock_connection.channel.return_value = mock_channel
        mock_channel.declare_exchange.return_value = mock_exchange
        mock_channel.declare_queue.return_value = mock_queue
        mock_connect.return_value = mock_connection

        mock_handler = AsyncMock()
        consumer = RabbitMQConsumer(diagram_handler=mock_handler)

        # Act
        await consumer.start()

        # Assert
        mock_connect.assert_called_once()
        mock_queue.bind.assert_called_once()
        mock_queue.consume.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.infrastructure.messaging.consumer.get_settings")
    async def test_consumer_process_message_valid_event(self, mock_get_settings) -> None:
        """Test consumer processes valid DiagramaEnviado event."""
        # Arrange
        mock_settings = MagicMock()
        mock_settings.rabbitmq.url = "amqp://guest:guest@localhost/"
        mock_settings.rabbitmq.exchange_name = "archlens"
        mock_settings.rabbitmq.queue_name = "processing-queue"
        mock_get_settings.return_value = mock_settings

        mock_handler = AsyncMock()
        consumer = RabbitMQConsumer(diagram_handler=mock_handler)

        # Create a valid message
        message_body = {
            "event_type": "DiagramaEnviado",
            "payload": {
                "analise_id": "123",
                "diagrama_storage_path": "s3://bucket/diagram.png",
                "content_type": "image/png",
            },
        }

        mock_message = MagicMock()
        mock_message.body = json.dumps(message_body).encode()
        mock_message.process = MagicMock()
        mock_message.process.return_value.__aenter__ = AsyncMock()
        mock_message.process.return_value.__aexit__ = AsyncMock()

        # Act
        await consumer._process_message(mock_message)

        # Assert
        mock_handler.assert_called_once_with("123", "s3://bucket/diagram.png", "image/png")

    @pytest.mark.asyncio
    @patch("src.infrastructure.messaging.consumer.get_settings")
    async def test_consumer_process_message_wrong_event_type(self, mock_get_settings) -> None:
        """Test consumer ignores wrong event type."""
        # Arrange
        mock_settings = MagicMock()
        mock_settings.rabbitmq.url = "amqp://guest:guest@localhost/"
        mock_settings.rabbitmq.exchange_name = "archlens"
        mock_settings.rabbitmq.queue_name = "processing-queue"
        mock_get_settings.return_value = mock_settings

        mock_handler = AsyncMock()
        consumer = RabbitMQConsumer(diagram_handler=mock_handler)

        # Create a message with wrong event type
        message_body = {
            "event_type": "WrongEvent",
            "payload": {"analise_id": "123"},
        }

        mock_message = MagicMock()
        mock_message.body = json.dumps(message_body).encode()
        mock_message.process = MagicMock()
        mock_message.process.return_value.__aenter__ = AsyncMock()
        mock_message.process.return_value.__aexit__ = AsyncMock()

        # Act
        await consumer._process_message(mock_message)

        # Assert
        mock_handler.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.infrastructure.messaging.consumer.get_settings")
    async def test_consumer_process_message_invalid_json(self, mock_get_settings) -> None:
        """Test consumer handles invalid JSON."""
        # Arrange
        mock_settings = MagicMock()
        mock_settings.rabbitmq.url = "amqp://guest:guest@localhost/"
        mock_settings.rabbitmq.exchange_name = "archlens"
        mock_settings.rabbitmq.queue_name = "processing-queue"
        mock_get_settings.return_value = mock_settings

        mock_handler = AsyncMock()
        consumer = RabbitMQConsumer(diagram_handler=mock_handler)

        # Create a message with invalid JSON
        mock_message = MagicMock()
        mock_message.body = b"invalid json"
        mock_message.process = MagicMock()
        mock_message.process.return_value.__aenter__ = AsyncMock()
        mock_message.process.return_value.__aexit__ = AsyncMock()

        # Act
        await consumer._process_message(mock_message)

        # Assert
        mock_handler.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.infrastructure.messaging.consumer.aio_pika.connect_robust")
    @patch("src.infrastructure.messaging.consumer.get_settings")
    async def test_consumer_close(self, mock_get_settings, mock_connect) -> None:
        """Test consumer close disconnects from RabbitMQ."""
        # Arrange
        mock_settings = MagicMock()
        mock_settings.rabbitmq.url = "amqp://guest:guest@localhost/"
        mock_settings.rabbitmq.exchange_name = "archlens"
        mock_settings.rabbitmq.queue_name = "processing-queue"
        mock_get_settings.return_value = mock_settings

        mock_connection = AsyncMock()
        mock_connection.is_closed = False
        mock_channel = AsyncMock()
        mock_exchange = AsyncMock()
        mock_queue = AsyncMock()
        mock_connection.channel.return_value = mock_channel
        mock_channel.declare_exchange.return_value = mock_exchange
        mock_channel.declare_queue.return_value = mock_queue
        mock_connect.return_value = mock_connection

        mock_handler = AsyncMock()
        consumer = RabbitMQConsumer(diagram_handler=mock_handler)
        await consumer.start()

        # Act
        await consumer.close()

        # Assert
        mock_connection.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.infrastructure.messaging.consumer.get_settings")
    async def test_consumer_close_no_connection(self, mock_get_settings) -> None:
        """Test consumer close handles no connection."""
        # Arrange
        mock_settings = MagicMock()
        mock_settings.rabbitmq.url = "amqp://guest:guest@localhost/"
        mock_settings.rabbitmq.exchange_name = "archlens"
        mock_settings.rabbitmq.queue_name = "processing-queue"
        mock_get_settings.return_value = mock_settings

        mock_handler = AsyncMock()
        consumer = RabbitMQConsumer(diagram_handler=mock_handler)

        # Act
        await consumer.close()

        # Assert - Should not raise
