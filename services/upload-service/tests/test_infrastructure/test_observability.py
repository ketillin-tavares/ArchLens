"""Tests for observability modules (logging and metrics)."""

import time
from unittest.mock import MagicMock, patch

from src.infrastructure.observability.logging import _newrelic_linking_metadata, configure_logging
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


class TestNewrelicLinkingMetadata:
    """Tests for New Relic linking metadata injection."""

    def test_newrelic_linking_metadata_with_agent_unavailable(self) -> None:
        """Test linking metadata when New Relic agent is not available."""
        # Arrange
        event_dict = {"key": "value"}

        with patch("src.infrastructure.observability.logging._newrelic_agent", None):
            # Act
            result = _newrelic_linking_metadata(None, "method", event_dict)

            # Assert
            assert result == event_dict
            assert "trace.id" not in result

    def test_newrelic_linking_metadata_with_agent_available_full_metadata(self) -> None:
        """Test linking metadata injection when agent has complete metadata."""
        # Arrange
        event_dict = {"key": "value"}
        mock_agent = MagicMock()
        mock_agent.get_linking_metadata.return_value = {
            "entity.name": "upload-service",
            "entity.guid": "test-guid-123",
            "trace.id": "test-trace-id",
            "span.id": "test-span-id",
        }

        with patch("src.infrastructure.observability.logging._newrelic_agent", mock_agent):
            # Act
            result = _newrelic_linking_metadata(None, "method", event_dict)

            # Assert
            assert result["nr.entityName"] == "upload-service"
            assert result["nr.entityGuid"] == "test-guid-123"
            assert result["trace.id"] == "test-trace-id"
            assert result["span.id"] == "test-span-id"

    def test_newrelic_linking_metadata_with_empty_metadata(self) -> None:
        """Test linking metadata when agent returns empty metadata."""
        # Arrange
        event_dict = {"key": "value"}
        mock_agent = MagicMock()
        mock_agent.get_linking_metadata.return_value = None

        with patch("src.infrastructure.observability.logging._newrelic_agent", mock_agent):
            # Act
            result = _newrelic_linking_metadata(None, "method", event_dict)

            # Assert
            assert result == event_dict

    def test_newrelic_linking_metadata_with_partial_metadata(self) -> None:
        """Test linking metadata injection with partial metadata."""
        # Arrange
        event_dict = {"key": "value"}
        mock_agent = MagicMock()
        mock_agent.get_linking_metadata.return_value = {
            "entity.name": "upload-service",
            "trace.id": "test-trace-id",
        }

        with patch("src.infrastructure.observability.logging._newrelic_agent", mock_agent):
            # Act
            result = _newrelic_linking_metadata(None, "method", event_dict)

            # Assert
            assert result["nr.entityName"] == "upload-service"
            assert result["trace.id"] == "test-trace-id"
            assert "span.id" not in result


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
