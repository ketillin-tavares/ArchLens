"""Tests for domain events."""

import uuid
from datetime import UTC, datetime

import pytest

from src.domain.events import DiagramaEnviado


class TestDiagramaEnviado:
    """Tests for DiagramaEnviado event."""

    def test_create_diagrama_enviado_event(self) -> None:
        """Test creating a DiagramaEnviado event."""
        # Arrange
        analise_id = uuid.uuid4()
        storage_path = "diagramas/2026/03/30/test-uuid.png"
        content_type = "image/png"
        tamanho_bytes = 5120

        # Act
        evento = DiagramaEnviado(
            analise_id=analise_id,
            diagrama_storage_path=storage_path,
            content_type=content_type,
            tamanho_bytes=tamanho_bytes,
        )

        # Assert
        assert evento.event_type == "DiagramaEnviado"
        assert evento.analise_id == analise_id
        assert evento.diagrama_storage_path == storage_path
        assert evento.content_type == content_type
        assert evento.tamanho_bytes == tamanho_bytes
        assert evento.timestamp is not None

    def test_diagrama_enviado_has_default_timestamp(self) -> None:
        """Test that DiagramaEnviado has a default timestamp."""
        # Arrange
        analise_id = uuid.uuid4()

        # Act
        evento = DiagramaEnviado(
            analise_id=analise_id,
            diagrama_storage_path="diagramas/2026/03/30/uuid.png",
            content_type="image/png",
            tamanho_bytes=1024,
        )

        # Assert
        assert evento.timestamp is not None
        assert isinstance(evento.timestamp, datetime)

    def test_diagrama_enviado_with_explicit_timestamp(self) -> None:
        """Test creating DiagramaEnviado with explicit timestamp."""
        # Arrange
        analise_id = uuid.uuid4()
        timestamp = datetime(2026, 1, 15, 10, 30, 45, tzinfo=UTC)

        # Act
        evento = DiagramaEnviado(
            analise_id=analise_id,
            diagrama_storage_path="diagramas/2026/03/30/uuid.png",
            content_type="image/png",
            tamanho_bytes=1024,
            timestamp=timestamp,
        )

        # Assert
        assert evento.timestamp == timestamp

    def test_to_message_serializes_event(self) -> None:
        """Test that to_message() properly serializes the event."""
        # Arrange
        analise_id = uuid.uuid4()
        storage_path = "diagramas/2026/03/30/test-uuid.png"
        content_type = "image/png"
        tamanho_bytes = 5120
        timestamp = datetime(2026, 1, 15, 10, 30, 45, tzinfo=UTC)

        evento = DiagramaEnviado(
            analise_id=analise_id,
            diagrama_storage_path=storage_path,
            content_type=content_type,
            tamanho_bytes=tamanho_bytes,
            timestamp=timestamp,
        )

        # Act
        message = evento.to_message()

        # Assert
        assert message["event_type"] == "DiagramaEnviado"
        assert message["timestamp"] == timestamp.isoformat()
        assert "payload" in message
        assert message["payload"]["analise_id"] == str(analise_id)
        assert message["payload"]["diagrama_storage_path"] == storage_path
        assert message["payload"]["content_type"] == content_type
        assert message["payload"]["tamanho_bytes"] == tamanho_bytes

    def test_to_message_converts_uuid_to_string(self) -> None:
        """Test that to_message() converts UUID to string in payload."""
        # Arrange
        analise_id = uuid.uuid4()
        evento = DiagramaEnviado(
            analise_id=analise_id,
            diagrama_storage_path="diagramas/2026/03/30/uuid.png",
            content_type="image/png",
            tamanho_bytes=1024,
        )

        # Act
        message = evento.to_message()

        # Assert
        assert isinstance(message["payload"]["analise_id"], str)
        assert message["payload"]["analise_id"] == str(analise_id)

    def test_to_message_uses_iso_format_timestamp(self) -> None:
        """Test that to_message() uses ISO format for timestamp."""
        # Arrange
        timestamp = datetime(2026, 3, 30, 15, 45, 30, 123456, tzinfo=UTC)
        evento = DiagramaEnviado(
            analise_id=uuid.uuid4(),
            diagrama_storage_path="diagramas/2026/03/30/uuid.png",
            content_type="image/png",
            tamanho_bytes=1024,
            timestamp=timestamp,
        )

        # Act
        message = evento.to_message()

        # Assert
        assert message["timestamp"] == "2026-03-30T15:45:30.123456+00:00"

    def test_to_message_structure_for_rabbitmq(self) -> None:
        """Test that to_message() structure matches RabbitMQ message format."""
        # Arrange
        analise_id = uuid.uuid4()
        storage_path = "diagramas/2026/03/30/uuid.png"
        content_type = "image/png"
        tamanho_bytes = 2048

        evento = DiagramaEnviado(
            analise_id=analise_id,
            diagrama_storage_path=storage_path,
            content_type=content_type,
            tamanho_bytes=tamanho_bytes,
        )

        # Act
        message = evento.to_message()

        # Assert - Verify message structure for RabbitMQ
        assert isinstance(message, dict)
        assert "event_type" in message
        assert "timestamp" in message
        assert "payload" in message
        assert isinstance(message["payload"], dict)
        assert len(message["payload"]) == 4  # analise_id, path, type, size

    def test_tamanho_bytes_validation(self) -> None:
        """Test that tamanho_bytes must be greater than 0."""
        # Act & Assert
        with pytest.raises(ValueError):
            DiagramaEnviado(
                analise_id=uuid.uuid4(),
                diagrama_storage_path="diagramas/2026/03/30/uuid.png",
                content_type="image/png",
                tamanho_bytes=0,
            )
