"""Tests for interface gateways."""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities import Analise, Diagrama
from src.domain.value_objects import StatusAnalise
from src.infrastructure.models.analise_model import AnaliseModel
from src.infrastructure.models.diagrama_model import DiagramaModel
from src.interface.gateways.analise_repository_gateway import SQLAlchemyAnaliseRepository
from src.interface.gateways.diagrama_repository_gateway import SQLAlchemyDiagramaRepository
from src.interface.gateways.event_publisher_gateway import RabbitMQEventPublisherGateway
from src.interface.gateways.file_storage_gateway import S3FileStorageGateway


class TestSQLAlchemyAnaliseRepository:
    """Tests for SQLAlchemy-based Analise repository."""

    @pytest.mark.asyncio
    async def test_salvar_creates_analise(self) -> None:
        """Test saving a new analysis."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)

        repo = SQLAlchemyAnaliseRepository(mock_session)
        analise_id = uuid.uuid4()
        diagrama_id = uuid.uuid4()

        analise = Analise(
            id=analise_id,
            diagrama_id=diagrama_id,
            status=StatusAnalise.RECEBIDO,
        )

        # Act
        result = await repo.salvar(analise)

        # Assert
        assert result == analise
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_buscar_por_id_found(self) -> None:
        """Test finding an analysis by ID."""
        # Arrange
        analise_id = uuid.uuid4()
        diagrama_id = uuid.uuid4()

        mock_model = AnaliseModel(
            id=analise_id,
            diagrama_id=diagrama_id,
            status=StatusAnalise.RECEBIDO.value,
            criado_em=datetime.now(UTC),
            atualizado_em=datetime.now(UTC),
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_model

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = SQLAlchemyAnaliseRepository(mock_session)

        # Act
        result = await repo.buscar_por_id(analise_id)

        # Assert
        assert result is not None
        assert result.id == analise_id
        assert result.diagrama_id == diagrama_id

    @pytest.mark.asyncio
    async def test_buscar_por_id_not_found(self) -> None:
        """Test finding an analysis by ID when it does not exist."""
        # Arrange
        analise_id = uuid.uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = SQLAlchemyAnaliseRepository(mock_session)

        # Act
        result = await repo.buscar_por_id(analise_id)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_atualizar_status_success(self) -> None:
        """Test updating analysis status successfully."""
        # Arrange
        analise_id = uuid.uuid4()
        diagrama_id = uuid.uuid4()
        novo_status = StatusAnalise.EM_PROCESSAMENTO

        mock_model = AnaliseModel(
            id=analise_id,
            diagrama_id=diagrama_id,
            status=StatusAnalise.RECEBIDO.value,
            criado_em=datetime.now(UTC),
            atualizado_em=datetime.now(UTC),
        )

        # Create a mock result for the first execute call (buscar_por_id)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_model

        # Mock session with side effects for multiple execute calls
        mock_session = AsyncMock(spec=AsyncSession)
        # First call returns the model, second call returns None (update doesn't return the model)
        mock_session.execute = AsyncMock(side_effect=[mock_result, MagicMock()])

        repo = SQLAlchemyAnaliseRepository(mock_session)

        # Act
        result = await repo.atualizar_status(analise_id, novo_status)

        # Assert
        assert result is True
        # Should be called twice - once for buscar_por_id, once for update
        assert mock_session.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_atualizar_status_com_erro(self) -> None:
        """Test updating analysis status with error details."""
        # Arrange
        analise_id = uuid.uuid4()
        diagrama_id = uuid.uuid4()
        novo_status = StatusAnalise.ERRO
        erro_detalhe = "Falha ao processar"

        mock_model = AnaliseModel(
            id=analise_id,
            diagrama_id=diagrama_id,
            status=StatusAnalise.EM_PROCESSAMENTO.value,
            criado_em=datetime.now(UTC),
            atualizado_em=datetime.now(UTC),
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_model

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock(side_effect=[mock_result, MagicMock()])

        repo = SQLAlchemyAnaliseRepository(mock_session)

        # Act
        result = await repo.atualizar_status(analise_id, novo_status, erro_detalhe)

        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_atualizar_status_not_found(self) -> None:
        """Test updating status of non-existent analysis."""
        # Arrange
        analise_id = uuid.uuid4()
        novo_status = StatusAnalise.EM_PROCESSAMENTO

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = SQLAlchemyAnaliseRepository(mock_session)

        # Act
        result = await repo.atualizar_status(analise_id, novo_status)

        # Assert
        assert result is False


class TestSQLAlchemyDiagramaRepository:
    """Tests for SQLAlchemy-based Diagrama repository."""

    @pytest.mark.asyncio
    async def test_salvar_creates_diagrama(self) -> None:
        """Test saving a new diagram."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)

        repo = SQLAlchemyDiagramaRepository(mock_session)
        diagrama_id = uuid.uuid4()

        diagrama = Diagrama(
            id=diagrama_id,
            nome_original="arquitetura.png",
            storage_path="diagramas/test-uuid.png",
            content_type="image/png",
            tamanho_bytes=1024,
        )

        # Act
        result = await repo.salvar(diagrama)

        # Assert
        assert result == diagrama
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_buscar_por_id_found(self) -> None:
        """Test finding a diagram by ID."""
        # Arrange
        diagrama_id = uuid.uuid4()

        mock_model = DiagramaModel(
            id=diagrama_id,
            nome_original="arquitetura.png",
            storage_path="diagramas/test-uuid.png",
            content_type="image/png",
            tamanho_bytes=1024,
            criado_em=datetime.now(UTC),
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_model

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = SQLAlchemyDiagramaRepository(mock_session)

        # Act
        result = await repo.buscar_por_id(diagrama_id)

        # Assert
        assert result is not None
        assert result.id == diagrama_id

    @pytest.mark.asyncio
    async def test_buscar_por_id_not_found(self) -> None:
        """Test finding a diagram by ID when it does not exist."""
        # Arrange
        diagrama_id = uuid.uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = SQLAlchemyDiagramaRepository(mock_session)

        # Act
        result = await repo.buscar_por_id(diagrama_id)

        # Assert
        assert result is None


class TestS3FileStorageGateway:
    """Tests for S3 file storage gateway."""

    @pytest.mark.asyncio
    async def test_upload_file(self) -> None:
        """Test uploading a file to S3."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.upload_file.return_value = "diagramas/test-uuid.png"

        gateway = S3FileStorageGateway(client=mock_client)
        file_bytes = b"fake image data"
        storage_path = "diagramas/test-uuid.png"
        content_type = "image/png"

        # Act
        result = await gateway.upload_file(file_bytes, storage_path, content_type)

        # Assert
        assert result == "diagramas/test-uuid.png"
        mock_client.upload_file.assert_called_once_with(file_bytes, storage_path, content_type)


class TestRabbitMQEventPublisherGateway:
    """Tests for RabbitMQ event publisher gateway."""

    @pytest.mark.asyncio
    async def test_publish_event(self) -> None:
        """Test publishing an event to RabbitMQ."""
        # Arrange
        mock_publisher = AsyncMock()
        mock_publisher.publish_event = AsyncMock()

        gateway = RabbitMQEventPublisherGateway(mock_publisher)

        event_type = "DiagramaEnviado"
        routing_key = "diagrama.enviado"
        payload = {
            "analise_id": "test-uuid-123",
            "diagrama_id": "test-uuid-456",
        }

        # Act
        await gateway.publish_event(event_type, routing_key, payload)

        # Assert
        mock_publisher.publish_event.assert_called_once_with(event_type, routing_key, payload)

    @pytest.mark.asyncio
    async def test_publish_event_without_publisher(self) -> None:
        """Test publishing an event when publisher is not configured."""
        # Arrange
        gateway = RabbitMQEventPublisherGateway()

        event_type = "DiagramaEnviado"
        routing_key = "diagrama.enviado"
        payload = {"analise_id": "test-uuid-123"}

        # Act & Assert
        with pytest.raises(RuntimeError, match="Publisher RabbitMQ não configurado"):
            await gateway.publish_event(event_type, routing_key, payload)

    def test_set_publisher(self) -> None:
        """Test setting the publisher."""
        # Arrange
        gateway = RabbitMQEventPublisherGateway()
        mock_publisher = AsyncMock()

        # Act
        gateway.set_publisher(mock_publisher)

        # Assert
        assert gateway._publisher == mock_publisher
