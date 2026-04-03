"""Unit tests for domain events."""

import uuid
from datetime import datetime

from src.domain.events import AnaliseConcluida, AnaliseFalhou, ProcessamentoIniciado


class TestProcessamentoIniciadoEvent:
    """Tests for ProcessamentoIniciado event."""

    def test_processamento_iniciado_creation(self) -> None:
        """Test creating a ProcessamentoIniciado event."""
        # Arrange
        analise_id = uuid.uuid4()

        # Act
        event = ProcessamentoIniciado(analise_id=analise_id)

        # Assert
        assert event.event_type == "ProcessamentoIniciado"
        assert event.analise_id == analise_id
        assert isinstance(event.timestamp, datetime)

    def test_processamento_iniciado_to_message(self) -> None:
        """Test serializing ProcessamentoIniciado to message format."""
        # Arrange
        analise_id = uuid.uuid4()
        event = ProcessamentoIniciado(analise_id=analise_id)

        # Act
        message = event.to_message()

        # Assert
        assert message["event_type"] == "ProcessamentoIniciado"
        assert message["payload"]["analise_id"] == str(analise_id)
        assert "timestamp" in message

    def test_processamento_iniciado_timestamp_iso_format(self) -> None:
        """Test that timestamp is in ISO format in message."""
        # Arrange
        analise_id = uuid.uuid4()
        event = ProcessamentoIniciado(analise_id=analise_id)

        # Act
        message = event.to_message()

        # Assert
        timestamp_str = message["timestamp"]
        # Should be ISO format string
        assert isinstance(timestamp_str, str)
        assert "T" in timestamp_str


class TestAnaliseConcluídaEvent:
    """Tests for AnaliseConcluida event."""

    def test_analise_concluida_creation_minimal(self) -> None:
        """Test creating AnaliseConcluida with minimal data."""
        # Arrange
        analise_id = uuid.uuid4()

        # Act
        event = AnaliseConcluida(analise_id=analise_id)

        # Assert
        assert event.event_type == "AnaliseConcluida"
        assert event.analise_id == analise_id
        assert event.componentes == []
        assert event.riscos == []
        assert isinstance(event.timestamp, datetime)

    def test_analise_concluida_creation_with_results(self) -> None:
        """Test creating AnaliseConcluida with results."""
        # Arrange
        analise_id = uuid.uuid4()
        componentes = [
            {"id": "comp_1", "nome": "API Gateway", "tipo": "api_gateway"},
            {"id": "comp_2", "nome": "Database", "tipo": "database"},
        ]
        riscos = [
            {
                "id": "risk_1",
                "descricao": "Single point of failure",
                "severidade": "alta",
            }
        ]

        # Act
        event = AnaliseConcluida(
            analise_id=analise_id,
            componentes=componentes,
            riscos=riscos,
        )

        # Assert
        assert event.analise_id == analise_id
        assert len(event.componentes) == 2
        assert len(event.riscos) == 1
        assert event.componentes[0]["nome"] == "API Gateway"
        assert event.riscos[0]["severidade"] == "alta"

    def test_analise_concluida_to_message(self) -> None:
        """Test serializing AnaliseConcluida to message format."""
        # Arrange
        analise_id = uuid.uuid4()
        componentes = [{"id": "comp_1", "nome": "API Gateway"}]
        riscos = [{"id": "risk_1", "descricao": "Risk"}]
        event = AnaliseConcluida(
            analise_id=analise_id,
            componentes=componentes,
            riscos=riscos,
        )

        # Act
        message = event.to_message()

        # Assert
        assert message["event_type"] == "AnaliseConcluida"
        assert message["payload"]["analise_id"] == str(analise_id)
        assert message["payload"]["componentes"] == componentes
        assert message["payload"]["riscos"] == riscos
        assert "timestamp" in message

    def test_analise_concluida_empty_results(self) -> None:
        """Test AnaliseConcluida with empty results."""
        # Arrange
        analise_id = uuid.uuid4()
        event = AnaliseConcluida(analise_id=analise_id)

        # Act
        message = event.to_message()

        # Assert
        assert message["payload"]["componentes"] == []
        assert message["payload"]["riscos"] == []


class TestAnaliseFalhouEvent:
    """Tests for AnaliseFalhou event."""

    def test_analise_falhou_creation_minimal(self) -> None:
        """Test creating AnaliseFalhou with minimal data."""
        # Arrange
        analise_id = uuid.uuid4()
        erro_detalhe = "LLM timeout"

        # Act
        event = AnaliseFalhou(
            analise_id=analise_id,
            erro_detalhe=erro_detalhe,
        )

        # Assert
        assert event.event_type == "AnaliseFalhou"
        assert event.analise_id == analise_id
        assert event.erro_detalhe == erro_detalhe
        assert event.tentativa == 1
        assert isinstance(event.timestamp, datetime)

    def test_analise_falhou_creation_with_tentativa(self) -> None:
        """Test creating AnaliseFalhou with tentativa counter."""
        # Arrange
        analise_id = uuid.uuid4()
        erro_detalhe = "Network error"
        tentativa = 3

        # Act
        event = AnaliseFalhou(
            analise_id=analise_id,
            erro_detalhe=erro_detalhe,
            tentativa=tentativa,
        )

        # Assert
        assert event.tentativa == tentativa
        assert event.erro_detalhe == erro_detalhe

    def test_analise_falhou_to_message(self) -> None:
        """Test serializing AnaliseFalhou to message format."""
        # Arrange
        analise_id = uuid.uuid4()
        erro_detalhe = "LLM returned invalid JSON"
        tentativa = 2
        event = AnaliseFalhou(
            analise_id=analise_id,
            erro_detalhe=erro_detalhe,
            tentativa=tentativa,
        )

        # Act
        message = event.to_message()

        # Assert
        assert message["event_type"] == "AnaliseFalhou"
        assert message["payload"]["analise_id"] == str(analise_id)
        assert message["payload"]["erro_detalhe"] == erro_detalhe
        assert message["payload"]["tentativa"] == tentativa
        assert "timestamp" in message

    def test_analise_falhou_with_long_error_message(self) -> None:
        """Test AnaliseFalhou with a long error message."""
        # Arrange
        analise_id = uuid.uuid4()
        long_error = "E" * 1000

        # Act
        event = AnaliseFalhou(
            analise_id=analise_id,
            erro_detalhe=long_error,
        )

        # Assert
        assert event.erro_detalhe == long_error
        assert len(event.erro_detalhe) == 1000
