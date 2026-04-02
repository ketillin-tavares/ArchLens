"""Unit tests for domain events."""

import uuid
from datetime import UTC, datetime

import pytest

from src.domain.events import RelatorioGerado


class TestRelatorioGeradoEvent:
    """Tests for the RelatorioGerado domain event."""

    def test_event_creation_with_defaults(self) -> None:
        """Test creating a RelatorioGerado event with default values."""
        # Arrange
        analise_id = uuid.uuid4()
        relatorio_id = uuid.uuid4()

        # Act
        event = RelatorioGerado(analise_id=analise_id, relatorio_id=relatorio_id)

        # Assert
        assert event.event_type == "RelatorioGerado"
        assert event.analise_id == analise_id
        assert event.relatorio_id == relatorio_id
        assert isinstance(event.timestamp, datetime)

    def test_event_with_custom_timestamp(self) -> None:
        """Test creating an event with a custom timestamp."""
        # Arrange
        analise_id = uuid.uuid4()
        relatorio_id = uuid.uuid4()
        custom_timestamp = datetime(2026, 4, 1, 12, 30, 45, tzinfo=UTC)

        # Act
        event = RelatorioGerado(
            analise_id=analise_id,
            relatorio_id=relatorio_id,
            timestamp=custom_timestamp,
        )

        # Assert
        assert event.timestamp == custom_timestamp

    def test_to_message_serialization(self) -> None:
        """Test the to_message() method serializes correctly."""
        # Arrange
        analise_id = uuid.uuid4()
        relatorio_id = uuid.uuid4()
        event = RelatorioGerado(analise_id=analise_id, relatorio_id=relatorio_id)

        # Act
        message = event.to_message()

        # Assert
        assert isinstance(message, dict)
        assert message["event_type"] == "RelatorioGerado"
        assert "timestamp" in message
        assert isinstance(message["timestamp"], str)
        assert "payload" in message
        assert isinstance(message["payload"], dict)

    def test_to_message_payload_format(self) -> None:
        """Test that to_message() payload contains correct fields."""
        # Arrange
        analise_id = uuid.uuid4()
        relatorio_id = uuid.uuid4()
        event = RelatorioGerado(analise_id=analise_id, relatorio_id=relatorio_id)

        # Act
        message = event.to_message()

        # Assert
        payload = message["payload"]
        assert payload["analise_id"] == str(analise_id)
        assert payload["relatorio_id"] == str(relatorio_id)

    def test_to_message_timestamp_iso_format(self) -> None:
        """Test that timestamp in to_message() is in ISO format."""
        # Arrange
        analise_id = uuid.uuid4()
        relatorio_id = uuid.uuid4()
        custom_timestamp = datetime(2026, 4, 1, 15, 30, 45, tzinfo=UTC)
        event = RelatorioGerado(
            analise_id=analise_id,
            relatorio_id=relatorio_id,
            timestamp=custom_timestamp,
        )

        # Act
        message = event.to_message()

        # Assert
        assert message["timestamp"] == "2026-04-01T15:30:45+00:00"

    def test_event_pydantic_validation(self) -> None:
        """Test that RelatorioGerado validates required fields."""
        # Arrange & Act & Assert
        with pytest.raises(ValueError):
            RelatorioGerado(
                analise_id=uuid.uuid4(),
                # Missing relatorio_id (required)
            )

        with pytest.raises(ValueError):
            RelatorioGerado(
                # Missing analise_id (required)
                relatorio_id=uuid.uuid4(),
            )

    def test_to_message_returns_new_dict(self) -> None:
        """Test that to_message() returns a new dictionary instance."""
        # Arrange
        analise_id = uuid.uuid4()
        relatorio_id = uuid.uuid4()
        event = RelatorioGerado(analise_id=analise_id, relatorio_id=relatorio_id)

        # Act
        message1 = event.to_message()
        message2 = event.to_message()

        # Assert
        assert message1 == message2
        assert message1 is not message2  # Different object instances

    def test_event_with_multiple_generations(self) -> None:
        """Test creating multiple events with same IDs."""
        # Arrange
        analise_id = uuid.uuid4()
        relatorio_id = uuid.uuid4()

        # Act
        event1 = RelatorioGerado(analise_id=analise_id, relatorio_id=relatorio_id)
        event2 = RelatorioGerado(analise_id=analise_id, relatorio_id=relatorio_id)

        # Assert
        assert event1.analise_id == event2.analise_id
        assert event1.relatorio_id == event2.relatorio_id
        # Timestamps should be different or very close
        assert isinstance(event1.timestamp, datetime)
        assert isinstance(event2.timestamp, datetime)
