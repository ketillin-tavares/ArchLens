"""Unit tests for observability infrastructure."""

import time
from unittest.mock import MagicMock, patch

from src.infrastructure.observability.logging import _newrelic_linking_metadata, configure_logging
from src.infrastructure.observability.metrics import MetricsRecorder


class TestConfigureLogging:
    """Tests for logging configuration."""

    def test_configure_logging_default_level(self) -> None:
        """Test configure_logging with default level."""
        # Act
        configure_logging()

        # Assert - Should not raise

    def test_configure_logging_debug_level(self) -> None:
        """Test configure_logging with DEBUG level."""
        # Act
        configure_logging(log_level="DEBUG")

        # Assert - Should not raise

    def test_configure_logging_info_level(self) -> None:
        """Test configure_logging with INFO level."""
        # Act
        configure_logging(log_level="INFO")

        # Assert - Should not raise

    def test_configure_logging_warning_level(self) -> None:
        """Test configure_logging with WARNING level."""
        # Act
        configure_logging(log_level="WARNING")

        # Assert - Should not raise

    def test_configure_logging_error_level(self) -> None:
        """Test configure_logging with ERROR level."""
        # Act
        configure_logging(log_level="ERROR")

        # Assert - Should not raise

    @patch("src.infrastructure.observability.logging._newrelic_agent")
    def test_newrelic_linking_metadata_available(self, mock_agent) -> None:
        """Test _newrelic_linking_metadata when New Relic is available."""
        # Arrange
        mock_agent.get_linking_metadata.return_value = {
            "entity.name": "processing-service",
            "entity.guid": "test-guid",
            "trace.id": "trace-123",
            "span.id": "span-456",
        }

        logger = MagicMock()
        event_dict = {}

        # Act
        result = _newrelic_linking_metadata(logger, "info", event_dict)

        # Assert
        assert "nr.entityName" in result
        assert "nr.entityGuid" in result
        assert "trace.id" in result
        assert "span.id" in result

    def test_newrelic_linking_metadata_unavailable(self) -> None:
        """Test _newrelic_linking_metadata when New Relic is unavailable."""
        # Arrange
        with patch("src.infrastructure.observability.logging._newrelic_agent", None):
            logger = MagicMock()
            event_dict = {"test": "data"}

            # Act
            result = _newrelic_linking_metadata(logger, "info", event_dict)

            # Assert
            assert result == event_dict


class TestMetricsRecorder:
    """Tests for MetricsRecorder."""

    @patch("src.infrastructure.observability.metrics._newrelic_agent")
    def test_record_component_count(self, mock_agent) -> None:
        """Test record_component_count."""
        # Arrange
        mock_agent.record_custom_metric = MagicMock()

        # Act
        MetricsRecorder.record_component_count(5)

        # Assert
        mock_agent.record_custom_metric.assert_called_once_with("Custom/AI/ComponentCount", 5)

    @patch("src.infrastructure.observability.metrics._newrelic_agent")
    def test_record_risk_count(self, mock_agent) -> None:
        """Test record_risk_count."""
        # Arrange
        mock_agent.record_custom_metric = MagicMock()

        # Act
        MetricsRecorder.record_risk_count(3)

        # Assert
        mock_agent.record_custom_metric.assert_called_once_with("Custom/AI/RiskCount", 3)

    @patch("src.infrastructure.observability.metrics._newrelic_agent")
    def test_record_avg_confidence(self, mock_agent) -> None:
        """Test record_avg_confidence."""
        # Arrange
        mock_agent.record_custom_metric = MagicMock()

        # Act
        MetricsRecorder.record_avg_confidence(0.85)

        # Assert
        mock_agent.record_custom_metric.assert_called_once_with("Custom/AI/AvgConfidence", 0.85)

    @patch("src.infrastructure.observability.metrics._newrelic_agent")
    def test_record_latency(self, mock_agent) -> None:
        """Test record_latency."""
        # Arrange
        mock_agent.record_custom_metric = MagicMock()

        # Act
        MetricsRecorder.record_latency(2.5)

        # Assert
        mock_agent.record_custom_metric.assert_called_once_with("Custom/AI/LatencySeconds", 2.5)

    @patch("src.infrastructure.observability.metrics._newrelic_agent")
    def test_record_validation_retries(self, mock_agent) -> None:
        """Test record_validation_retries."""
        # Arrange
        mock_agent.record_custom_metric = MagicMock()

        # Act
        MetricsRecorder.record_validation_retries(2)

        # Assert
        mock_agent.record_custom_metric.assert_called_once_with("Custom/AI/ValidationRetries", 2)

    @patch("src.infrastructure.observability.metrics._newrelic_agent")
    def test_record_analise_iniciada(self, mock_agent) -> None:
        """Test record_analise_iniciada."""
        # Arrange
        mock_agent.record_custom_event = MagicMock()

        # Act
        MetricsRecorder.record_analise_iniciada("test-id")

        # Assert
        mock_agent.record_custom_event.assert_called_once_with("AnaliseIniciada", {"analise_id": "test-id"})

    @patch("src.infrastructure.observability.metrics._newrelic_agent")
    def test_record_analise_sucesso(self, mock_agent) -> None:
        """Test record_analise_sucesso."""
        # Arrange
        mock_agent.record_custom_event = MagicMock()

        # Act
        MetricsRecorder.record_analise_sucesso("test-id", 1.5, 5, 2)

        # Assert
        mock_agent.record_custom_event.assert_called_once()
        call_args = mock_agent.record_custom_event.call_args
        assert call_args[0][0] == "AnaliseSucesso"
        assert call_args[0][1]["analise_id"] == "test-id"

    @patch("src.infrastructure.observability.metrics._newrelic_agent")
    def test_record_analise_falha(self, mock_agent) -> None:
        """Test record_analise_falha."""
        # Arrange
        mock_agent.record_custom_event = MagicMock()

        # Act
        MetricsRecorder.record_analise_falha("test-id", "Error message", "LLMApiError")

        # Assert
        mock_agent.record_custom_event.assert_called_once()
        call_args = mock_agent.record_custom_event.call_args
        assert call_args[0][0] == "AnaliseFalha"
        assert call_args[0][1]["analise_id"] == "test-id"

    def test_start_timer(self) -> None:
        """Test start_timer returns timestamp."""
        # Act
        start = MetricsRecorder.start_timer()

        # Assert
        assert isinstance(start, float)
        assert start > 0

    def test_elapsed_time(self) -> None:
        """Test elapsed calculates time difference."""
        # Arrange
        start = MetricsRecorder.start_timer()
        time.sleep(0.01)  # Sleep 10ms

        # Act
        elapsed = MetricsRecorder.elapsed(start)

        # Assert
        assert isinstance(elapsed, float)
        assert elapsed >= 0.01

    @patch("src.infrastructure.observability.metrics._newrelic_agent", None)
    def test_metrics_without_newrelic(self) -> None:
        """Test metrics work without New Relic agent."""
        # Act & Assert - Should not raise
        MetricsRecorder.record_component_count(5)
        MetricsRecorder.record_risk_count(3)
        MetricsRecorder.record_analise_iniciada("test-id")
