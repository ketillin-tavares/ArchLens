"""Unit tests for observability metrics."""

import time
from unittest.mock import MagicMock, patch

from src.infrastructure.observability.logging import _newrelic_linking_metadata, configure_logging
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
        mock_agent.record_custom_metric = MagicMock()

        # Act
        _record_newrelic_metric("Custom/Test/Metric", 42.0)

        # Assert
        mock_agent.record_custom_metric.assert_called_once_with("Custom/Test/Metric", 42.0)

    @patch("src.infrastructure.observability.metrics._newrelic_agent")
    def test_record_newrelic_metric_with_different_values(self, mock_agent: MagicMock) -> None:
        """Test recording metrics with different metric names and values."""
        # Arrange
        mock_agent.record_custom_metric = MagicMock()

        # Act
        _record_newrelic_metric("Custom/Metric1", 10.5)
        _record_newrelic_metric("Custom/Metric2", 99.9)
        _record_newrelic_metric("Custom/Metric3", 0.0)

        # Assert
        assert mock_agent.record_custom_metric.call_count == 3
        calls = mock_agent.record_custom_metric.call_args_list
        assert calls[0][0] == ("Custom/Metric1", 10.5)
        assert calls[1][0] == ("Custom/Metric2", 99.9)
        assert calls[2][0] == ("Custom/Metric3", 0.0)


class TestLogging:
    """Tests for logging configuration."""

    @patch("src.infrastructure.observability.logging.structlog.configure")
    def test_configure_logging_with_default_level(self, mock_configure: MagicMock) -> None:
        """Test configure_logging with default INFO level."""
        # Act
        configure_logging()

        # Assert
        mock_configure.assert_called_once()
        call_kwargs = mock_configure.call_args[1]
        assert "processors" in call_kwargs
        assert "wrapper_class" in call_kwargs
        assert "context_class" in call_kwargs
        assert "logger_factory" in call_kwargs

    @patch("src.infrastructure.observability.logging.structlog.configure")
    def test_configure_logging_with_debug_level(self, mock_configure: MagicMock) -> None:
        """Test configure_logging with DEBUG level."""
        # Act
        configure_logging(log_level="DEBUG")

        # Assert
        mock_configure.assert_called_once()

    @patch("src.infrastructure.observability.logging.structlog.configure")
    def test_configure_logging_with_error_level(self, mock_configure: MagicMock) -> None:
        """Test configure_logging with ERROR level."""
        # Act
        configure_logging(log_level="ERROR")

        # Assert
        mock_configure.assert_called_once()

    @patch("src.infrastructure.observability.logging.structlog.configure")
    def test_configure_logging_processors_list(self, mock_configure: MagicMock) -> None:
        """Test that configure_logging includes required processors."""
        # Act
        configure_logging()

        # Assert
        call_kwargs = mock_configure.call_args[1]
        processors = call_kwargs["processors"]

        # Verify that processors is a list with items
        assert isinstance(processors, list)
        assert len(processors) > 0

        # Verify JSON renderer is included
        processor_names = [type(p).__name__ for p in processors]
        assert "JSONRenderer" in processor_names


class TestNewRelicLinkingMetadata:
    """Tests for _newrelic_linking_metadata function."""

    def test_newrelic_linking_metadata_when_agent_is_none(self) -> None:
        """Test that _newrelic_linking_metadata returns event_dict unchanged when agent is None."""
        # Arrange
        with patch("src.infrastructure.observability.logging._newrelic_agent", None):
            event_dict = {"level": "info", "message": "test"}

            # Act
            result = _newrelic_linking_metadata(None, "info", event_dict)

            # Assert
            assert result == event_dict

    @patch("src.infrastructure.observability.logging._newrelic_agent")
    def test_newrelic_linking_metadata_injects_trace_context(self, mock_agent: MagicMock) -> None:
        """Test that _newrelic_linking_metadata injects trace context when available."""
        # Arrange
        mock_agent.get_linking_metadata.return_value = {
            "entity.name": "test-entity",
            "entity.guid": "test-guid-123",
            "trace.id": "trace-abc",
            "span.id": "span-xyz",
        }
        event_dict = {"level": "info", "message": "test"}

        # Act
        result = _newrelic_linking_metadata(None, "info", event_dict)

        # Assert
        assert result["nr.entityName"] == "test-entity"
        assert result["nr.entityGuid"] == "test-guid-123"
        assert result["trace.id"] == "trace-abc"
        assert result["span.id"] == "span-xyz"

    @patch("src.infrastructure.observability.logging._newrelic_agent")
    def test_newrelic_linking_metadata_empty_metadata(self, mock_agent: MagicMock) -> None:
        """Test that _newrelic_linking_metadata handles empty metadata."""
        # Arrange
        mock_agent.get_linking_metadata.return_value = {}
        event_dict = {"level": "info", "message": "test"}

        # Act
        result = _newrelic_linking_metadata(None, "info", event_dict)

        # Assert - should not add trace/span if empty
        assert "trace.id" not in result
        assert "span.id" not in result

    @patch("src.infrastructure.observability.logging._newrelic_agent")
    def test_newrelic_linking_metadata_partial_metadata(self, mock_agent: MagicMock) -> None:
        """Test that _newrelic_linking_metadata handles partial metadata."""
        # Arrange
        mock_agent.get_linking_metadata.return_value = {
            "entity.name": "entity",
            "trace.id": "trace-123",
        }
        event_dict = {"level": "info", "message": "test"}

        # Act
        result = _newrelic_linking_metadata(None, "info", event_dict)

        # Assert
        assert result["nr.entityName"] == "entity"
        assert result["trace.id"] == "trace-123"
        assert "span.id" not in result  # Not in metadata, so not added
