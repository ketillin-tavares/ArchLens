"""Tests for messaging infrastructure."""

from unittest.mock import AsyncMock

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


class TestRabbitMQPublisher:
    """Tests for RabbitMQ publisher."""

    def test_publisher_initialization(self) -> None:
        """Test publisher initialization."""
        # Act
        publisher = RabbitMQPublisher()

        # Assert
        assert publisher is not None

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
