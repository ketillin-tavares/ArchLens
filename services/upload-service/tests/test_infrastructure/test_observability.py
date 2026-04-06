"""Tests for observability modules (logging and metrics)."""

import time
from unittest.mock import MagicMock, patch

from src.infrastructure.observability.logging import (
    _StdlibLogSink,
    _StructuredLogger,
    configure_logging,
    get_logger,
)
from src.infrastructure.observability.metrics import MetricsRecorder, _record_newrelic_metric


class TestConfigureLogging:
    """Tests for logging configuration."""

    def test_configure_logging_with_debug_level(self) -> None:
        """Test logging configuration with DEBUG level."""
        # Act
        configure_logging(log_level="DEBUG")

        # Assert - no exception should be raised
        assert True

    def test_configure_logging_with_info_level(self) -> None:
        """Test logging configuration with INFO level."""
        # Act
        configure_logging(log_level="INFO")

        # Assert
        assert True

    def test_configure_logging_with_warning_level(self) -> None:
        """Test logging configuration with WARNING level."""
        # Act
        configure_logging(log_level="WARNING")

        # Assert
        assert True

    def test_configure_logging_with_error_level(self) -> None:
        """Test logging configuration with ERROR level."""
        # Act
        configure_logging(log_level="ERROR")

        # Assert
        assert True

    def test_configure_logging_default_level(self) -> None:
        """Test logging configuration with default level."""
        # Act
        configure_logging()

        # Assert
        assert True


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

    @patch("src.infrastructure.observability.logging._newrelic_agent")
    def test_write_does_not_call_notice_error_on_info_level(self, mock_agent: MagicMock) -> None:
        """Test that write() does not call notice_error for INFO level."""
        # Arrange
        sink = _StdlibLogSink("INFO")
        sink._stdlib_logger = MagicMock()

        mock_message = MagicMock()
        mock_message.record = {
            "level": MagicMock(no=20, name="INFO"),
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


class TestRecordNewrelicMetric:
    """Tests for recording New Relic metrics."""

    def test_record_newrelic_metric_with_agent_available(self) -> None:
        """Test recording metric when New Relic agent is available."""
        # Arrange
        mock_agent = MagicMock()

        with patch("src.infrastructure.observability.metrics._newrelic_agent", mock_agent):
            # Act
            _record_newrelic_metric("Custom/Test/Metric", 42.5)

            # Assert
            mock_agent.record_custom_metric.assert_called_once_with("Custom/Test/Metric", 42.5)

    def test_record_newrelic_metric_with_agent_unavailable(self) -> None:
        """Test recording metric when New Relic agent is not available."""
        # Arrange
        with patch("src.infrastructure.observability.metrics._newrelic_agent", None):
            # Act - should not raise exception
            _record_newrelic_metric("Custom/Test/Metric", 42.5)

            # Assert
            assert True


class TestMetricsRecorder:
    """Tests for MetricsRecorder class."""

    def test_record_analise_por_status(self) -> None:
        """Test recording analysis status metric."""
        # Arrange
        mock_agent = MagicMock()

        with patch("src.infrastructure.observability.metrics._newrelic_agent", mock_agent):
            # Act
            MetricsRecorder.record_analise_por_status("recebido")

            # Assert
            mock_agent.record_custom_metric.assert_called_once_with("Custom/Analise/Status/recebido", 1)

    def test_record_upload_tamanho(self) -> None:
        """Test recording upload size metric."""
        # Arrange
        mock_agent = MagicMock()

        with patch("src.infrastructure.observability.metrics._newrelic_agent", mock_agent):
            # Act
            MetricsRecorder.record_upload_tamanho(5242880)  # 5MB

            # Assert
            mock_agent.record_custom_metric.assert_called_once_with("Custom/Upload/TamanhoBytes", 5242880)

    def test_record_tempo_processamento(self) -> None:
        """Test recording processing time metric."""
        # Arrange
        mock_agent = MagicMock()
        analise_id = "test-uuid-123"
        duracao = 12.5

        with patch("src.infrastructure.observability.metrics._newrelic_agent", mock_agent):
            # Act
            MetricsRecorder.record_tempo_processamento(analise_id, duracao)

            # Assert
            mock_agent.record_custom_metric.assert_called_once_with("Custom/Analise/TempoProcessamento", duracao)

    def test_record_falha(self) -> None:
        """Test recording failure metric."""
        # Arrange
        mock_agent = MagicMock()

        with patch("src.infrastructure.observability.metrics._newrelic_agent", mock_agent):
            # Act
            MetricsRecorder.record_falha()

            # Assert
            mock_agent.record_custom_metric.assert_called_once_with("Custom/Analise/Falhas", 1)

    def test_start_timer(self) -> None:
        """Test starting a timer."""
        # Act
        start_time = MetricsRecorder.start_timer()

        # Assert
        assert isinstance(start_time, float)
        assert start_time > 0

    def test_elapsed_time(self) -> None:
        """Test calculating elapsed time."""
        # Arrange
        start_time = MetricsRecorder.start_timer()
        time.sleep(0.1)  # Sleep for 100ms

        # Act
        elapsed = MetricsRecorder.elapsed(start_time)

        # Assert
        assert elapsed >= 0.1
        assert elapsed < 0.5  # Should not take much longer

    def test_elapsed_time_zero(self) -> None:
        """Test elapsed time when called immediately."""
        # Arrange
        start_time = MetricsRecorder.start_timer()

        # Act
        elapsed = MetricsRecorder.elapsed(start_time)

        # Assert
        assert elapsed >= 0
        assert elapsed < 0.1
