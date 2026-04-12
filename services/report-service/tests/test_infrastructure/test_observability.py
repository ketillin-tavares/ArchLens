"""Unit tests for observability metrics."""

import time
from unittest.mock import MagicMock, patch

from src.infrastructure.observability.logging import (
    _StdlibLogSink,
    _StructuredLogger,
    configure_logging,
    get_logger,
)
from src.infrastructure.observability.metrics import MetricsRecorder, _record_newrelic_metric


class TestMetricsRecorder:
    """Tests for the MetricsRecorder class."""

    def test_start_timer_returns_float(self) -> None:
        """Test that start_timer returns a numeric value."""
        # Act
        start = MetricsRecorder.start_timer()

        # Assert
        assert isinstance(start, float)
        assert start > 0

    def test_elapsed_calculates_duration(self) -> None:
        """Test that elapsed calculates correct duration."""
        # Arrange
        start = MetricsRecorder.start_timer()
        time.sleep(0.05)  # Sleep for 50ms

        # Act
        elapsed = MetricsRecorder.elapsed(start)

        # Assert
        assert elapsed >= 0.04  # Allow some tolerance
        assert elapsed < 0.2  # Should not be too long

    def test_elapsed_with_immediate_call(self) -> None:
        """Test elapsed with very small time difference."""
        # Arrange
        start = MetricsRecorder.start_timer()

        # Act
        elapsed = MetricsRecorder.elapsed(start)

        # Assert
        assert elapsed >= 0
        assert elapsed < 0.01  # Should be very small

    @patch("src.infrastructure.observability.metrics._record_newrelic_metric")
    def test_record_relatorio_gerado(self, mock_record: MagicMock) -> None:
        """Test recording a report generation metric."""
        # Act
        MetricsRecorder.record_relatorio_gerado()

        # Assert
        mock_record.assert_called_once_with("Custom/Relatorio/Gerados", 1)

    @patch("src.infrastructure.observability.metrics._record_newrelic_metric")
    def test_record_tempo_geracao(self, mock_record: MagicMock) -> None:
        """Test recording report generation time metric."""
        # Arrange
        analise_id = "test-id"
        duration = 2.5

        # Act
        MetricsRecorder.record_tempo_geracao(analise_id, duration)

        # Assert
        mock_record.assert_called_once_with("Custom/Relatorio/TempoGeracao", duration)

    @patch("src.infrastructure.observability.metrics._record_newrelic_metric")
    def test_record_relatorio_duplicado(self, mock_record: MagicMock) -> None:
        """Test recording duplicate report metric."""
        # Act
        MetricsRecorder.record_relatorio_duplicado()

        # Assert
        mock_record.assert_called_once_with("Custom/Relatorio/Duplicados", 1)

    @patch("src.infrastructure.observability.metrics._record_newrelic_metric")
    def test_record_relatorio_consultado(self, mock_record: MagicMock) -> None:
        """Test recording report query metric."""
        # Act
        MetricsRecorder.record_relatorio_consultado()

        # Assert
        mock_record.assert_called_once_with("Custom/Relatorio/Consultas", 1)

    def test_timer_accuracy(self) -> None:
        """Test that timer measurements are accurate."""
        # Arrange
        start = MetricsRecorder.start_timer()
        time.sleep(0.1)  # Sleep for 100ms

        # Act
        elapsed = MetricsRecorder.elapsed(start)

        # Assert
        assert 0.08 <= elapsed <= 0.15  # Allow tolerance
        assert elapsed > 0.09  # Should be at least ~100ms

    @patch("src.infrastructure.observability.metrics._record_newrelic_metric")
    def test_record_tempo_geracao_with_zero_duration(self, mock_record: MagicMock) -> None:
        """Test recording with zero duration."""
        # Act
        MetricsRecorder.record_tempo_geracao("test-id", 0.0)

        # Assert
        mock_record.assert_called_once_with("Custom/Relatorio/TempoGeracao", 0.0)

    @patch("src.infrastructure.observability.metrics._record_newrelic_metric")
    def test_record_multiple_metrics(self, mock_record: MagicMock) -> None:
        """Test recording multiple metrics in sequence."""
        # Act
        MetricsRecorder.record_relatorio_gerado()
        MetricsRecorder.record_tempo_geracao("id1", 1.5)
        MetricsRecorder.record_relatorio_consultado()

        # Assert
        assert mock_record.call_count == 3
        calls = mock_record.call_args_list
        assert calls[0][0][0] == "Custom/Relatorio/Gerados"
        assert calls[1][0][0] == "Custom/Relatorio/TempoGeracao"
        assert calls[2][0][0] == "Custom/Relatorio/Consultas"


class TestRecordNewRelicMetric:
    """Tests for the _record_newrelic_metric function."""

    def test_record_newrelic_metric_when_agent_is_none(self) -> None:
        """Test that _record_newrelic_metric handles None agent gracefully."""
        # Arrange - mock the module-level _newrelic_agent as None
        with patch("src.infrastructure.observability.metrics._newrelic_agent", None):
            # Act & Assert - should not raise
            _record_newrelic_metric("Custom/Test/Metric", 42.0)

    @patch("src.infrastructure.observability.metrics._newrelic_agent")
    def test_record_newrelic_metric_when_agent_available(self, mock_agent: MagicMock) -> None:
        """Test that _record_newrelic_metric calls agent when available."""
        # Arrange
        mock_app = MagicMock()
        mock_agent.application.return_value = mock_app

        # Act
        _record_newrelic_metric("Custom/Test/Metric", 42.0)

        # Assert
        mock_app.record_custom_metric.assert_called_once_with("Custom/Test/Metric", 42.0)

    @patch("src.infrastructure.observability.metrics._newrelic_agent")
    def test_record_newrelic_metric_with_different_values(self, mock_agent: MagicMock) -> None:
        """Test recording metrics with different metric names and values."""
        # Arrange
        mock_app = MagicMock()
        mock_agent.application.return_value = mock_app

        # Act
        _record_newrelic_metric("Custom/Metric1", 10.5)
        _record_newrelic_metric("Custom/Metric2", 99.9)
        _record_newrelic_metric("Custom/Metric3", 0.0)

        # Assert
        assert mock_app.record_custom_metric.call_count == 3
        calls = mock_app.record_custom_metric.call_args_list
        assert calls[0][0] == ("Custom/Metric1", 10.5)
        assert calls[1][0] == ("Custom/Metric2", 99.9)
        assert calls[2][0] == ("Custom/Metric3", 0.0)


class TestConfigureLogging:
    """Tests for loguru logging configuration."""

    @patch("src.infrastructure.observability.logging.logger")
    def test_configure_logging_removes_default_handler(self, mock_logger: MagicMock) -> None:
        """Test that configure_logging removes the default loguru handler."""
        # Act
        configure_logging()

        # Assert
        mock_logger.remove.assert_called_once()

    @patch("src.infrastructure.observability.logging.logger")
    def test_configure_logging_adds_two_sinks(self, mock_logger: MagicMock) -> None:
        """Test that configure_logging adds terminal and stdlib sinks."""
        # Act
        configure_logging()

        # Assert
        assert mock_logger.add.call_count == 2

    @patch("src.infrastructure.observability.logging.logger")
    def test_configure_logging_with_debug_level(self, mock_logger: MagicMock) -> None:
        """Test configure_logging with DEBUG level."""
        # Act
        configure_logging(log_level="DEBUG")

        # Assert
        mock_logger.remove.assert_called_once()
        assert mock_logger.add.call_count == 2
        first_call_kwargs = mock_logger.add.call_args_list[0][1]
        assert first_call_kwargs["level"] == "DEBUG"

    @patch("src.infrastructure.observability.logging.logger")
    def test_configure_logging_with_error_level(self, mock_logger: MagicMock) -> None:
        """Test configure_logging with ERROR level."""
        # Act
        configure_logging(log_level="ERROR")

        # Assert
        first_call_kwargs = mock_logger.add.call_args_list[0][1]
        assert first_call_kwargs["level"] == "ERROR"


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
    def test_error_delegates_to_loguru(self, mock_logger: MagicMock) -> None:
        """Test that error() calls loguru with bind and message."""
        # Arrange
        structured_logger = _StructuredLogger()

        # Act
        structured_logger.error("erro_teste", detalhe="falha")

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

    def test_get_logger_returns_singleton(self) -> None:
        """Test that get_logger always returns the same instance."""
        # Act
        logger_a = get_logger()
        logger_b = get_logger()

        # Assert
        assert logger_a is logger_b


class TestStdlibLogSink:
    """Tests for _StdlibLogSink that routes logs to stdlib logging."""

    def test_creates_stdlib_logger_with_correct_level(self) -> None:
        """Test that _StdlibLogSink configures stdlib logger level."""
        # Arrange
        import logging as stdlib_logging

        # Act
        sink = _StdlibLogSink("WARNING")

        # Assert
        assert sink._stdlib_logger.level == stdlib_logging.WARNING

    @patch("src.infrastructure.observability.logging._newrelic_agent", None)
    def test_write_forwards_to_stdlib_logger(self) -> None:
        """Test that write() creates and handles a stdlib LogRecord."""
        # Arrange
        sink = _StdlibLogSink("INFO")
        sink._stdlib_logger = MagicMock()

        mock_message = MagicMock()
        mock_level = MagicMock()
        mock_level.no = 20
        mock_level.name = "INFO"
        mock_message.record = {
            "level": mock_level,
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
        mock_level = MagicMock()
        mock_level.no = 40
        mock_level.name = "ERROR"
        mock_message.record = {
            "level": mock_level,
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

    @patch("src.infrastructure.observability.logging._newrelic_agent")
    def test_write_does_not_call_notice_error_on_info_level(self, mock_agent: MagicMock) -> None:
        """Test that write() does not call notice_error for INFO level."""
        # Arrange
        sink = _StdlibLogSink("INFO")
        sink._stdlib_logger = MagicMock()

        mock_message = MagicMock()
        mock_level = MagicMock()
        mock_level.no = 20
        mock_level.name = "INFO"
        mock_message.record = {
            "level": mock_level,
            "file": MagicMock(path="/test.py"),
            "line": 10,
            "message": "tudo_ok",
            "extra": {},
            "exception": None,
        }

        # Act
        sink.write(mock_message)

        # Assert
        mock_agent.notice_error.assert_not_called()
