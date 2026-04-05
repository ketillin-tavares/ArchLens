"""Unit tests for interface gateways."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

from src.domain.entities import Relatorio
from src.infrastructure.messaging.publisher import RabbitMQPublisher
from src.interface.gateways.event_publisher_gateway import RabbitMQEventPublisherGateway
from src.interface.gateways.file_storage_gateway import S3FileStorageGateway
from src.interface.gateways.markdown_report_writer_gateway import ReportWriterGateway
from src.interface.gateways.relatorio_repository_gateway import SQLAlchemyRelatorioRepository


class TestRabbitMQEventPublisherGateway:
    """Tests for the RabbitMQEventPublisherGateway adapter."""

    def test_gateway_initialization_with_publisher(self) -> None:
        """Test initializing gateway with a publisher."""
        # Arrange
        mock_publisher = AsyncMock(spec=RabbitMQPublisher)

        # Act
        gateway = RabbitMQEventPublisherGateway(publisher=mock_publisher)

        # Assert
        assert gateway._publisher == mock_publisher

    def test_gateway_initialization_without_publisher(self) -> None:
        """Test initializing gateway without a publisher."""
        # Act
        gateway = RabbitMQEventPublisherGateway()

        # Assert
        assert gateway._publisher is None

    def test_set_publisher(self) -> None:
        """Test setting publisher after initialization."""
        # Arrange
        gateway = RabbitMQEventPublisherGateway()
        mock_publisher = AsyncMock(spec=RabbitMQPublisher)

        # Act
        gateway.set_publisher(mock_publisher)

        # Assert
        assert gateway._publisher == mock_publisher

    async def test_publish_event_delegates_to_publisher(self) -> None:
        """Test that publish_event delegates to the underlying publisher."""
        # Arrange
        mock_publisher = AsyncMock(spec=RabbitMQPublisher)
        gateway = RabbitMQEventPublisherGateway(publisher=mock_publisher)

        event_type = "TestEvent"
        routing_key = "test.routing.key"
        payload = {"event_id": "123", "data": "test"}

        # Act
        await gateway.publish_event(event_type, routing_key, payload)

        # Assert
        mock_publisher.publish_event.assert_called_once_with(event_type, routing_key, payload)

    async def test_publish_event_raises_without_publisher(self) -> None:
        """Test that publish_event raises if publisher not configured."""
        # Arrange
        gateway = RabbitMQEventPublisherGateway()

        # Act & Assert
        with pytest.raises(RuntimeError, match="não configurado"):
            await gateway.publish_event("event", "key", {})

    async def test_publish_event_after_set_publisher(self) -> None:
        """Test publishing after setting publisher."""
        # Arrange
        gateway = RabbitMQEventPublisherGateway()
        mock_publisher = AsyncMock(spec=RabbitMQPublisher)
        gateway.set_publisher(mock_publisher)

        # Act
        await gateway.publish_event("TestEvent", "test.key", {"data": "test"})

        # Assert
        mock_publisher.publish_event.assert_called_once()

    async def test_publish_multiple_events(self) -> None:
        """Test publishing multiple events."""
        # Arrange
        mock_publisher = AsyncMock(spec=RabbitMQPublisher)
        gateway = RabbitMQEventPublisherGateway(publisher=mock_publisher)

        # Act
        await gateway.publish_event("Event1", "routing.1", {"id": 1})
        await gateway.publish_event("Event2", "routing.2", {"id": 2})
        await gateway.publish_event("Event3", "routing.3", {"id": 3})

        # Assert
        assert mock_publisher.publish_event.call_count == 3

    async def test_gateway_implements_port_interface(self) -> None:
        """Test that gateway implements the EventPublisher port interface."""
        # Arrange & Act
        from src.application.ports import EventPublisher

        mock_publisher = AsyncMock(spec=RabbitMQPublisher)
        gateway = RabbitMQEventPublisherGateway(publisher=mock_publisher)

        # Assert
        assert isinstance(gateway, EventPublisher)


class TestSQLAlchemyRelatorioRepository:
    """Tests for the SQLAlchemyRelatorioRepository adapter."""

    async def test_repository_initialization(self) -> None:
        """Test that repository initializes correctly."""
        # Arrange
        mock_session = AsyncMock()

        # Act
        repo = SQLAlchemyRelatorioRepository(session=mock_session)

        # Assert
        assert repo._session == mock_session

    async def test_salvar_persists_relatorio(self) -> None:
        """Test that salvar persists a relatorio entity."""
        # Arrange
        mock_session = AsyncMock()
        mock_session.flush = AsyncMock()
        relatorio = Relatorio(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            analise_id=UUID("87654321-4321-8765-4321-876543218765"),
            titulo="Test Report",
            resumo="Test Summary",
            conteudo={"key": "value"},
            criado_em=datetime.now(),
        )

        repo = SQLAlchemyRelatorioRepository(session=mock_session)

        # Act
        result = await repo.salvar(relatorio)

        # Assert
        assert result == relatorio
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    async def test_buscar_por_analise_id_returns_none_when_not_found(self) -> None:
        """Test that buscar_por_analise_id returns None when relatorio not found."""
        # Arrange
        mock_session = AsyncMock()
        mock_execute = MagicMock()
        mock_execute.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_execute)

        repo = SQLAlchemyRelatorioRepository(session=mock_session)
        analise_id = UUID("87654321-4321-8765-4321-876543218765")

        # Act
        result = await repo.buscar_por_analise_id(analise_id)

        # Assert
        assert result is None
        mock_session.execute.assert_called_once()

    async def test_buscar_por_analise_id_returns_relatorio_when_found(self) -> None:
        """Test that buscar_por_analise_id returns relatorio when found."""
        # Arrange
        from src.infrastructure.models.relatorio_model import RelatorioModel

        mock_session = AsyncMock()
        mock_execute = MagicMock()

        relatorio_id = UUID("12345678-1234-5678-1234-567812345678")
        analise_id = UUID("87654321-4321-8765-4321-876543218765")
        now = datetime.now()

        mock_model = MagicMock(spec=RelatorioModel)
        mock_model.id = relatorio_id
        mock_model.analise_id = analise_id
        mock_model.titulo = "Test Report"
        mock_model.resumo = "Test Summary"
        mock_model.conteudo = {"key": "value"}
        mock_model.s3_key = None
        mock_model.criado_em = now

        mock_execute.scalar_one_or_none.return_value = mock_model
        mock_session.execute = AsyncMock(return_value=mock_execute)

        repo = SQLAlchemyRelatorioRepository(session=mock_session)

        # Act
        result = await repo.buscar_por_analise_id(analise_id)

        # Assert
        assert result is not None
        assert result.id == relatorio_id
        assert result.analise_id == analise_id
        assert result.titulo == "Test Report"
        assert result.resumo == "Test Summary"
        assert result.conteudo == {"key": "value"}
        assert result.s3_key is None

    async def test_buscar_por_analise_id_handles_null_titulo_and_resumo(self) -> None:
        """Test that buscar_por_analise_id handles null titulo and resumo."""
        # Arrange
        from src.infrastructure.models.relatorio_model import RelatorioModel

        mock_session = AsyncMock()
        mock_execute = MagicMock()

        relatorio_id = UUID("12345678-1234-5678-1234-567812345678")
        analise_id = UUID("87654321-4321-8765-4321-876543218765")
        now = datetime.now()

        mock_model = MagicMock(spec=RelatorioModel)
        mock_model.id = relatorio_id
        mock_model.analise_id = analise_id
        mock_model.titulo = None  # Null titulo
        mock_model.resumo = None  # Null resumo
        mock_model.conteudo = {"key": "value"}
        mock_model.s3_key = None
        mock_model.criado_em = now

        mock_execute.scalar_one_or_none.return_value = mock_model
        mock_session.execute = AsyncMock(return_value=mock_execute)

        repo = SQLAlchemyRelatorioRepository(session=mock_session)

        # Act
        result = await repo.buscar_por_analise_id(analise_id)

        # Assert
        assert result is not None
        assert result.titulo == ""  # Should be empty string, not None
        assert result.resumo == ""  # Should be empty string, not None

    async def test_existe_por_analise_id_returns_true_when_exists(self) -> None:
        """Test that existe_por_analise_id returns True when relatorio exists."""
        # Arrange
        mock_session = AsyncMock()
        mock_execute = MagicMock()
        mock_execute.scalar.return_value = True
        mock_session.execute = AsyncMock(return_value=mock_execute)

        repo = SQLAlchemyRelatorioRepository(session=mock_session)
        analise_id = UUID("87654321-4321-8765-4321-876543218765")

        # Act
        result = await repo.existe_por_analise_id(analise_id)

        # Assert
        assert result is True
        mock_session.execute.assert_called_once()

    async def test_existe_por_analise_id_returns_false_when_not_exists(self) -> None:
        """Test that existe_por_analise_id returns False when relatorio does not exist."""
        # Arrange
        mock_session = AsyncMock()
        mock_execute = MagicMock()
        mock_execute.scalar.return_value = False
        mock_session.execute = AsyncMock(return_value=mock_execute)

        repo = SQLAlchemyRelatorioRepository(session=mock_session)
        analise_id = UUID("87654321-4321-8765-4321-876543218765")

        # Act
        result = await repo.existe_por_analise_id(analise_id)

        # Assert
        assert result is False

    async def test_existe_por_analise_id_handles_none_result(self) -> None:
        """Test that existe_por_analise_id handles None result from scalar."""
        # Arrange
        mock_session = AsyncMock()
        mock_execute = MagicMock()
        mock_execute.scalar.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_execute)

        repo = SQLAlchemyRelatorioRepository(session=mock_session)
        analise_id = UUID("87654321-4321-8765-4321-876543218765")

        # Act
        result = await repo.existe_por_analise_id(analise_id)

        # Assert
        assert result is False


class TestS3FileStorageGateway:
    """Tests for the S3FileStorageGateway adapter."""

    def test_gateway_initialization_with_client(self) -> None:
        """Test initializing gateway with a client."""
        # Arrange
        mock_client = AsyncMock()

        # Act
        gateway = S3FileStorageGateway(client=mock_client)

        # Assert
        assert gateway._client == mock_client

    def test_gateway_initialization_without_client(self) -> None:
        """Test initializing gateway without a client creates default S3StorageClient."""
        # Arrange & Act
        from src.infrastructure.storage.s3_client import S3StorageClient

        gateway = S3FileStorageGateway()

        # Assert
        assert gateway._client is not None
        assert isinstance(gateway._client, S3StorageClient)

    async def test_upload_text_delegates_to_client(self) -> None:
        """Test that upload_text delegates to the underlying S3 client."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.upload_text = AsyncMock(return_value="test-key")
        gateway = S3FileStorageGateway(client=mock_client)

        s3_key = "reports/test-report.md"
        content = "# Test Report"
        content_type = "text/markdown; charset=utf-8"

        # Act
        result = await gateway.upload_text(s3_key, content, content_type)

        # Assert
        assert result == "test-key"
        mock_client.upload_text.assert_called_once_with(s3_key, content, content_type)

    async def test_check_health_delegates_to_client(self) -> None:
        """Test that check_health delegates to the underlying S3 client."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.check_health = AsyncMock(return_value=True)
        gateway = S3FileStorageGateway(client=mock_client)

        # Act
        result = await gateway.check_health()

        # Assert
        assert result is True
        mock_client.check_health.assert_called_once()

    async def test_check_health_returns_false_on_failure(self) -> None:
        """Test that check_health returns False when client check fails."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.check_health = AsyncMock(return_value=False)
        gateway = S3FileStorageGateway(client=mock_client)

        # Act
        result = await gateway.check_health()

        # Assert
        assert result is False


class TestReportWriterGateway:
    """Tests for the ReportWriterGateway adapter."""

    def test_gateway_initialization_with_agent(self) -> None:
        """Test initializing gateway with an agent."""
        # Arrange
        mock_agent = AsyncMock()

        # Act
        gateway = ReportWriterGateway(agent=mock_agent)

        # Assert
        assert gateway._agent == mock_agent

    def test_gateway_initialization_without_agent(self) -> None:
        """Test initializing gateway without an agent creates default ReportWriterAgent."""
        # Arrange & Act
        from src.infrastructure.agents.report_writer_agent import ReportWriterAgent

        gateway = ReportWriterGateway()

        # Assert
        assert gateway._agent is not None
        assert isinstance(gateway._agent, ReportWriterAgent)

    async def test_generate_delegates_to_agent(self) -> None:
        """Test that generate delegates to the underlying ReportWriterAgent."""
        # Arrange
        from src.infrastructure.agents.schemas import MarkdownReportOutput

        mock_agent = AsyncMock()
        mock_output = MarkdownReportOutput(markdown="# Test Report\n" + "x" * 100)
        mock_agent.run = AsyncMock(return_value=mock_output)
        gateway = ReportWriterGateway(agent=mock_agent)

        titulo = "Test Report"
        resumo = "Test Summary"
        componentes = [{"id": "c1", "nome": "API"}]
        riscos = [{"id": "r1", "severidade": "alta"}]
        estatisticas = {"total": 1}

        # Act
        result = await gateway.generate(titulo, resumo, componentes, riscos, estatisticas)

        # Assert
        assert result == "# Test Report\n" + "x" * 100
        mock_agent.run.assert_called_once_with(
            titulo=titulo,
            resumo=resumo,
            componentes=componentes,
            riscos=riscos,
            estatisticas=estatisticas,
        )
