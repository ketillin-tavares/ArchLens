"""Unit tests for observability infrastructure."""

import time
from unittest.mock import MagicMock, patch

from src.infrastructure.observability.logging import (
    _StdlibLogSink,
    _StructuredLogger,
    configure_logging,
    get_logger,
)
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

    @patch("src.infrastructure.observability.logging.logger")
    def test_configure_logging_adds_two_sinks(self, mock_logger: MagicMock) -> None:
        """Test that configure_logging adds terminal and stdlib sinks."""
        # Act
        configure_logging()

        # Assert
        assert mock_logger.add.call_count == 2


class TestStructuredLogger:
    """Tests for _StructuredLogger adapter."""

    @patch("src.infrastructure.observability.logging.logger")
    def test_info_delegates_to_loguru(self, mock_logger: MagicMock) -> None:
        """Test that info() calls loguru with bind and message."""
        # Arrange
        structured_logger = _StructuredLogger()

        # Act
        structured_logger.info("evento_teste", chave="valor")

        # Assert
        mock_logger.opt.assert_called()

    @patch("src.infrastructure.observability.logging.logger")
    def test_exception_enables_traceback(self, mock_logger: MagicMock) -> None:
        """Test that exception() calls loguru with exception=True."""
        # Arrange
        structured_logger = _StructuredLogger()

        # Act
        structured_logger.exception("erro_com_traceback")

        # Assert
        mock_logger.opt.assert_called_once_with(depth=1, exception=True)

    def test_get_logger_returns_structured_logger(self) -> None:
        """Test that get_logger returns a _StructuredLogger instance."""
        # Act
        result = get_logger()

        # Assert
        assert isinstance(result, _StructuredLogger)


class TestStdlibLogSink:
    """Tests for _StdlibLogSink that routes logs to stdlib logging."""

    @patch("src.infrastructure.observability.logging._newrelic_agent", None)
    def test_write_forwards_to_stdlib_logger(self) -> None:
        """Test that write() creates and handles a stdlib LogRecord."""
        # Arrange
        sink = _StdlibLogSink("INFO")
        sink._stdlib_logger = MagicMock()

        mock_message = MagicMock()
        mock_message.record = {
            "level": MagicMock(no=20, name="INFO"),
            "file": MagicMock(path="/test.py"),
            "line": 42,
            "message": "test_message",
            "extra": {"analise_id": "abc-123"},
            "exception": None,
        }

        # Act
        sink.write(mock_message)

        # Assert
        sink._stdlib_logger.handle.assert_called_once()

    @patch("src.infrastructure.observability.logging._newrelic_agent")
    def test_write_calls_notice_error_on_error_level(self, mock_agent: MagicMock) -> None:
        """Test that write() calls notice_error for ERROR level logs."""
        # Arrange
        sink = _StdlibLogSink("INFO")
        sink._stdlib_logger = MagicMock()

        mock_message = MagicMock()
        mock_message.record = {
            "level": MagicMock(no=40, name="ERROR"),
            "file": MagicMock(path="/test.py"),
            "line": 10,
            "message": "falha_critica",
            "extra": {},
            "exception": None,
        }

        # Act
        sink.write(mock_message)

        # Assert
        mock_agent.notice_error.assert_called_once()


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
