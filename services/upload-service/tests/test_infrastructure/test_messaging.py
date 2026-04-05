"""Tests for messaging infrastructure."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import aio_pika
import pytest

from src.infrastructure.messaging.consumer import (
    EVENT_STATUS_MAP,
    ROUTING_KEYS,
    RabbitMQConsumer,
)
from src.infrastructure.messaging.publisher import RabbitMQPublisher


class TestEventStatusMap:
    """Tests for event status mapping."""

    def test_event_status_map_contents(self) -> None:
        """Test that event status map has expected events."""
        # Assert
        assert "ProcessamentoIniciado" in EVENT_STATUS_MAP
        assert "AnaliseConcluida" in EVENT_STATUS_MAP
        assert "AnaliseFalhou" in EVENT_STATUS_MAP
        assert "RelatorioGerado" in EVENT_STATUS_MAP

    def test_event_status_map_values(self) -> None:
        """Test that event status map has correct status values."""
        # Assert
        assert EVENT_STATUS_MAP["ProcessamentoIniciado"] == "em_processamento"
        assert EVENT_STATUS_MAP["AnaliseConcluida"] is None
        assert EVENT_STATUS_MAP["AnaliseFalhou"] == "erro"
        assert EVENT_STATUS_MAP["RelatorioGerado"] == "analisado"


class TestRoutingKeys:
    """Tests for routing keys configuration."""

    def test_routing_keys_list(self) -> None:
        """Test that routing keys list is properly configured."""
        # Assert
        assert isinstance(ROUTING_KEYS, list)
        assert len(ROUTING_KEYS) == 4
        assert "analise.processamento.iniciado" in ROUTING_KEYS
        assert "analise.processamento.concluida" in ROUTING_KEYS
        assert "analise.processamento.falhou" in ROUTING_KEYS
        assert "analise.relatorio.gerado" in ROUTING_KEYS


class TestRabbitMQConsumer:
    """Tests for RabbitMQ consumer."""

    def test_consumer_initialization(self) -> None:
        """Test consumer initialization."""
        # Arrange
        mock_handler = AsyncMock()

        # Act
        consumer = RabbitMQConsumer(status_update_handler=mock_handler)

        # Assert
        assert consumer._handler == mock_handler
        assert consumer._connection is None

    @pytest.mark.asyncio
    async def test_consumer_close(self) -> None:
        """Test closing consumer connection."""
        # Arrange
        mock_handler = AsyncMock()
        mock_connection = AsyncMock()
        mock_connection.is_closed = False

        consumer = RabbitMQConsumer(status_update_handler=mock_handler)
        consumer._connection = mock_connection

        # Act
        await consumer.close()

        # Assert
        mock_connection.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_consumer_close_already_closed(self) -> None:
        """Test closing consumer when connection is already closed."""
        # Arrange
        mock_handler = AsyncMock()
        mock_connection = AsyncMock()
        mock_connection.is_closed = True

        consumer = RabbitMQConsumer(status_update_handler=mock_handler)
        consumer._connection = mock_connection

        # Act
        await consumer.close()

        # Assert
        mock_connection.close.assert_not_called()

    @pytest.mark.asyncio
    async def test_consumer_close_no_connection(self) -> None:
        """Test closing consumer when there is no connection."""
        # Arrange
        mock_handler = AsyncMock()
        consumer = RabbitMQConsumer(status_update_handler=mock_handler)

        # Act & Assert - should not raise exception
        await consumer.close()

    @pytest.mark.asyncio
    @patch("src.infrastructure.messaging.consumer.aio_pika.connect_robust")
    async def test_start_connects_and_binds(self, mock_connect: AsyncMock) -> None:
        """Test that start connects to RabbitMQ, binds routing keys and starts consuming."""
        # Arrange
        mock_handler = AsyncMock()
        mock_connection = AsyncMock()
        mock_channel = AsyncMock()
        mock_exchange = AsyncMock()
        mock_queue = AsyncMock()

        mock_connect.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel
        mock_channel.get_exchange.return_value = mock_exchange
        mock_channel.declare_queue.return_value = mock_queue

        consumer = RabbitMQConsumer(status_update_handler=mock_handler)

        # Act
        await consumer.start()

        # Assert
        mock_connect.assert_called_once()
        mock_connection.channel.assert_called_once()
        mock_channel.set_qos.assert_called_once_with(prefetch_count=10)
        mock_channel.get_exchange.assert_called_once()
        mock_channel.declare_queue.assert_called_once()
        assert mock_queue.bind.call_count == len(ROUTING_KEYS)
        mock_queue.consume.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.infrastructure.messaging.consumer._newrelic_agent", None)
    async def test_process_message_processamento_iniciado(self) -> None:
        """Test processing a ProcessamentoIniciado event."""
        # Arrange
        mock_handler = AsyncMock()
        consumer = RabbitMQConsumer(status_update_handler=mock_handler)

        event_body = {
            "event_type": "ProcessamentoIniciado",
            "payload": {"analise_id": "test-123"},
        }

        mock_message = AsyncMock(spec=aio_pika.abc.AbstractIncomingMessage)
        mock_message.body = json.dumps(event_body).encode()
        mock_message.process = MagicMock(return_value=AsyncMock())
        mock_message.process.return_value.__aenter__ = AsyncMock()
        mock_message.process.return_value.__aexit__ = AsyncMock()

        # Act
        await consumer._process_message(mock_message)

        # Assert
        mock_handler.assert_called_once_with("test-123", "em_processamento", None, None)

    @pytest.mark.asyncio
    @patch("src.infrastructure.messaging.consumer._newrelic_agent", None)
    async def test_process_message_analise_falhou(self) -> None:
        """Test processing an AnaliseFalhou event with error details."""
        # Arrange
        mock_handler = AsyncMock()
        consumer = RabbitMQConsumer(status_update_handler=mock_handler)

        event_body = {
            "event_type": "AnaliseFalhou",
            "payload": {
                "analise_id": "test-123",
                "erro_detalhe": "Falha ao processar",
            },
        }

        mock_message = AsyncMock(spec=aio_pika.abc.AbstractIncomingMessage)
        mock_message.body = json.dumps(event_body).encode()
        mock_message.process = MagicMock(return_value=AsyncMock())
        mock_message.process.return_value.__aenter__ = AsyncMock()
        mock_message.process.return_value.__aexit__ = AsyncMock()

        # Act
        await consumer._process_message(mock_message)

        # Assert
        mock_handler.assert_called_once_with("test-123", "erro", "Falha ao processar", None)

    @pytest.mark.asyncio
    @patch("src.infrastructure.messaging.consumer._newrelic_agent", None)
    async def test_process_message_relatorio_gerado(self) -> None:
        """Test processing a RelatorioGerado event with s3_key."""
        # Arrange
        mock_handler = AsyncMock()
        consumer = RabbitMQConsumer(status_update_handler=mock_handler)

        event_body = {
            "event_type": "RelatorioGerado",
            "payload": {
                "analise_id": "test-123",
                "s3_key": "reports/test-123.md",
            },
        }

        mock_message = AsyncMock(spec=aio_pika.abc.AbstractIncomingMessage)
        mock_message.body = json.dumps(event_body).encode()
        mock_message.process = MagicMock(return_value=AsyncMock())
        mock_message.process.return_value.__aenter__ = AsyncMock()
        mock_message.process.return_value.__aexit__ = AsyncMock()

        # Act
        await consumer._process_message(mock_message)

        # Assert
        mock_handler.assert_called_once_with("test-123", "analisado", None, "reports/test-123.md")

    @pytest.mark.asyncio
    @patch("src.infrastructure.messaging.consumer._newrelic_agent", None)
    async def test_process_message_analise_concluida_ignored(self) -> None:
        """Test that AnaliseConcluida event is ignored (status is None)."""
        # Arrange
        mock_handler = AsyncMock()
        consumer = RabbitMQConsumer(status_update_handler=mock_handler)

        event_body = {
            "event_type": "AnaliseConcluida",
            "payload": {"analise_id": "test-123"},
        }

        mock_message = AsyncMock(spec=aio_pika.abc.AbstractIncomingMessage)
        mock_message.body = json.dumps(event_body).encode()
        mock_message.process = MagicMock(return_value=AsyncMock())
        mock_message.process.return_value.__aenter__ = AsyncMock()
        mock_message.process.return_value.__aexit__ = AsyncMock()

        # Act
        await consumer._process_message(mock_message)

        # Assert
        mock_handler.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.infrastructure.messaging.consumer._newrelic_agent", None)
    async def test_process_message_unknown_event_ignored(self) -> None:
        """Test that unknown event types are ignored."""
        # Arrange
        mock_handler = AsyncMock()
        consumer = RabbitMQConsumer(status_update_handler=mock_handler)

        event_body = {
            "event_type": "EventoDesconhecido",
            "payload": {"analise_id": "test-123"},
        }

        mock_message = AsyncMock(spec=aio_pika.abc.AbstractIncomingMessage)
        mock_message.body = json.dumps(event_body).encode()
        mock_message.process = MagicMock(return_value=AsyncMock())
        mock_message.process.return_value.__aenter__ = AsyncMock()
        mock_message.process.return_value.__aexit__ = AsyncMock()

        # Act
        await consumer._process_message(mock_message)

        # Assert
        mock_handler.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.infrastructure.messaging.consumer._newrelic_agent", None)
    async def test_process_message_malformed_json(self) -> None:
        """Test that malformed JSON is handled gracefully."""
        # Arrange
        mock_handler = AsyncMock()
        consumer = RabbitMQConsumer(status_update_handler=mock_handler)

        mock_message = AsyncMock(spec=aio_pika.abc.AbstractIncomingMessage)
        mock_message.body = b"not json {{"
        mock_message.process = MagicMock(return_value=AsyncMock())
        mock_message.process.return_value.__aenter__ = AsyncMock()
        mock_message.process.return_value.__aexit__ = AsyncMock()

        # Act & Assert — should not raise
        await consumer._process_message(mock_message)

        mock_handler.assert_not_called()


class TestRabbitMQPublisher:
    """Tests for RabbitMQ publisher."""

    def test_publisher_initialization(self) -> None:
        """Test publisher initialization."""
        # Act
        publisher = RabbitMQPublisher()

        # Assert
        assert publisher is not None

    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
    async def test_publisher_close(self) -> None:
        """Test closing publisher connection when no connection exists."""
        # Arrange
        publisher = RabbitMQPublisher()

        # Act & Assert - should not raise exception
        await publisher.close()

    @pytest.mark.asyncio
    async def test_publisher_close_with_connection(self) -> None:
        """Test closing publisher connection when connection exists."""
        # Arrange
        mock_connection = AsyncMock()
        mock_connection.is_closed = False
        publisher = RabbitMQPublisher()
        publisher._connection = mock_connection

        # Act
        await publisher.close()

        # Assert
        mock_connection.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_publisher_close_already_closed(self) -> None:
        """Test closing publisher when connection is already closed."""
        # Arrange
        mock_connection = AsyncMock()
        mock_connection.is_closed = True
        publisher = RabbitMQPublisher()
        publisher._connection = mock_connection

        # Act
        await publisher.close()

        # Assert
        mock_connection.close.assert_not_called()

    @pytest.mark.asyncio
    async def test_publisher_publish_event(self) -> None:
        """Test publishing an event."""
        # Arrange
        publisher = RabbitMQPublisher()
        mock_exchange = AsyncMock()
        publisher._exchange = mock_exchange

        event_type = "DiagramaEnviado"
        routing_key = "analise.diagrama.enviado"
        payload = {"analise_id": "test-uuid-123"}

        # Act
        await publisher.publish_event(event_type, routing_key, payload)

        # Assert
        mock_exchange.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_publisher_publish_event_without_connection(self) -> None:
        """Test publishing an event when not connected."""
        # Arrange
        publisher = RabbitMQPublisher()

        event_type = "DiagramaEnviado"
        routing_key = "analise.diagrama.enviado"
        payload = {"analise_id": "test-uuid-123"}

        # Act & Assert
        with pytest.raises(RuntimeError, match="Publisher não conectado"):
            await publisher.publish_event(event_type, routing_key, payload)
