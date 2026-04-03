"""Unit tests for interface gateways."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.domain.entities import Componente, Processamento, Risco, StatusProcessamento
from src.infrastructure.messaging.publisher import RabbitMQPublisher
from src.infrastructure.models import (
    ComponenteModel,
    ProcessamentoModel,
    RiscoComponenteModel,
    RiscoModel,
)
from src.infrastructure.storage import S3StorageClient
from src.interface.gateways.event_publisher_gateway import RabbitMQEventPublisherGateway
from src.interface.gateways.file_storage_gateway import S3FileStorageGateway
from src.interface.gateways.image_processor_gateway import FitzImageProcessorGateway
from src.interface.gateways.llm_client_gateway import PydanticAILLMClientGateway
from src.interface.gateways.processamento_repository_gateway import SQLAlchemyProcessamentoRepository


class TestRabbitMQEventPublisherGateway:
    """Tests for the RabbitMQEventPublisherGateway adapter."""

    def test_gateway_initialization(self) -> None:
        """Test initializing the event publisher gateway."""
        # Arrange
        mock_publisher = AsyncMock(spec=RabbitMQPublisher)

        # Act
        gateway = RabbitMQEventPublisherGateway(publisher=mock_publisher)

        # Assert
        assert gateway is not None

    def test_gateway_initialization_without_publisher(self) -> None:
        """Test initializing gateway without publisher."""
        # Act
        gateway = RabbitMQEventPublisherGateway()

        # Assert
        assert gateway is not None
        assert gateway._publisher is None

    def test_set_publisher(self) -> None:
        """Test setting publisher on gateway."""
        # Arrange
        gateway = RabbitMQEventPublisherGateway()
        mock_publisher = AsyncMock(spec=RabbitMQPublisher)

        # Act
        gateway.set_publisher(mock_publisher)

        # Assert
        assert gateway._publisher is mock_publisher

    @pytest.mark.asyncio
    async def test_publish_event_calls_publisher(self) -> None:
        """Test publish_event forwards to the publisher."""
        # Arrange
        mock_publisher = AsyncMock(spec=RabbitMQPublisher)
        gateway = RabbitMQEventPublisherGateway(publisher=mock_publisher)

        event_type = "ProcessamentoIniciado"
        routing_key = "analise.processamento.iniciado"
        payload = {"analise_id": "123"}

        # Act
        await gateway.publish_event(event_type, routing_key, payload)

        # Assert
        mock_publisher.publish_event.assert_called_once_with(event_type, routing_key, payload)

    @pytest.mark.asyncio
    async def test_publish_event_with_different_routing_keys(self) -> None:
        """Test publish_event with different routing keys."""
        # Arrange
        mock_publisher = AsyncMock(spec=RabbitMQPublisher)
        gateway = RabbitMQEventPublisherGateway(publisher=mock_publisher)

        routing_keys = [
            "analise.processamento.iniciado",
            "analise.processamento.concluida",
            "analise.processamento.falhou",
        ]

        # Act & Assert
        for routing_key in routing_keys:
            await gateway.publish_event("TestEvent", routing_key, {})
            mock_publisher.publish_event.assert_called()

    @pytest.mark.asyncio
    async def test_publish_event_raises_error_without_publisher(self) -> None:
        """Test publish_event raises error if publisher not set."""
        # Arrange
        gateway = RabbitMQEventPublisherGateway()

        # Act & Assert
        with pytest.raises(RuntimeError, match="Publisher RabbitMQ não configurado"):
            await gateway.publish_event("TestEvent", "test.key", {})


class TestS3FileStorageGateway:
    """Tests for the S3FileStorageGateway adapter."""

    def test_gateway_initialization(self) -> None:
        """Test initializing the S3 file storage gateway."""
        # Arrange
        mock_s3_client = AsyncMock(spec=S3StorageClient)

        # Act
        gateway = S3FileStorageGateway(s3_client=mock_s3_client)

        # Assert
        assert gateway is not None
        assert gateway._s3_client is mock_s3_client

    @pytest.mark.asyncio
    async def test_download_file(self) -> None:
        """Test download_file forwards to S3 client."""
        # Arrange
        mock_s3_client = AsyncMock(spec=S3StorageClient)
        file_content = b"test file content"
        mock_s3_client.download_file.return_value = file_content

        gateway = S3FileStorageGateway(s3_client=mock_s3_client)

        # Act
        result = await gateway.download_file("path/to/file.png")

        # Assert
        assert result == file_content
        mock_s3_client.download_file.assert_called_once_with("path/to/file.png")


class TestFitzImageProcessorGateway:
    """Tests for the FitzImageProcessorGateway adapter."""

    def test_gateway_initialization(self) -> None:
        """Test initializing the image processor gateway."""
        # Act
        gateway = FitzImageProcessorGateway()

        # Assert
        assert gateway is not None

    def test_normalize_image(self) -> None:
        """Test normalize forwards to processor."""
        # Arrange
        gateway = FitzImageProcessorGateway()
        file_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        content_type = "image/png"

        # Act
        with pytest.raises(Exception):
            # Will fail with incomplete PNG, but tests the gateway path
            gateway.normalize(file_bytes, content_type)


class TestPydanticAILLMClientGateway:
    """Tests for the PydanticAILLMClientGateway adapter."""

    @patch("src.interface.gateways.llm_client_gateway.PydanticAILLMClient")
    def test_gateway_initialization(self, mock_client_class) -> None:
        """Test initializing the LLM client gateway."""
        # Arrange
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        # Act
        gateway = PydanticAILLMClientGateway()

        # Assert
        assert gateway is not None
        assert gateway._client is not None

    @pytest.mark.asyncio
    @patch("src.interface.gateways.llm_client_gateway.PydanticAILLMClient")
    async def test_analyze_image_forwards_to_client(self, mock_client_class) -> None:
        """Test analyze_image forwards to LLM client."""
        # Arrange
        mock_client = AsyncMock()
        response_json = '{"componentes": [], "riscos": []}'
        mock_client.analyze_image.return_value = response_json
        mock_client_class.return_value = mock_client

        gateway = PydanticAILLMClientGateway()

        # Act
        result = await gateway.analyze_image("base64imagedata")

        # Assert
        assert result == response_json
        mock_client.analyze_image.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.interface.gateways.llm_client_gateway.PydanticAILLMClient")
    async def test_correct_json_forwards_to_client(self, mock_client_class) -> None:
        """Test correct_json forwards to LLM client."""
        # Arrange
        mock_client = AsyncMock()
        corrected_json = '{"componentes": [], "riscos": []}'
        mock_client.correct_json.return_value = corrected_json
        mock_client_class.return_value = mock_client

        gateway = PydanticAILLMClientGateway()

        # Act
        result = await gateway.correct_json('{"invalid": "json"}', "Error message")

        # Assert
        assert result == corrected_json
        mock_client.correct_json.assert_called_once()


class TestSQLAlchemyProcessamentoRepository:
    """Tests for the SQLAlchemyProcessamentoRepository adapter."""

    def test_repository_initialization(self) -> None:
        """Test repository initialization."""
        # Arrange
        mock_session = MagicMock()

        # Act
        repo = SQLAlchemyProcessamentoRepository(session=mock_session)

        # Assert
        assert repo is not None
        assert repo._session == mock_session

    def test_model_to_entity(self, analise_id: uuid.UUID) -> None:
        """Test _model_to_entity converts model to entity."""
        # Arrange
        processamento_id = uuid.uuid4()
        mock_model = ProcessamentoModel(
            id=processamento_id,
            analise_id=analise_id,
            status="concluido",
            tentativas=1,
            iniciado_em=None,
            concluido_em=None,
            erro_detalhe=None,
        )

        # Act
        entity = SQLAlchemyProcessamentoRepository._model_to_entity(mock_model)

        # Assert
        assert entity.id == processamento_id
        assert entity.analise_id == analise_id
        assert entity.status == StatusProcessamento.CONCLUIDO
        assert entity.tentativas == 1

    @pytest.mark.asyncio
    async def test_buscar_por_analise_id_found(
        self, analise_id: uuid.UUID, sample_processamento: Processamento
    ) -> None:
        """Test buscar_por_analise_id returns processamento when found."""
        # Arrange
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = ProcessamentoModel(
            id=sample_processamento.id,
            analise_id=analise_id,
            status=sample_processamento.status.value,
            tentativas=sample_processamento.tentativas,
            iniciado_em=sample_processamento.iniciado_em,
            concluido_em=sample_processamento.concluido_em,
            erro_detalhe=sample_processamento.erro_detalhe,
        )
        mock_session.execute.return_value = mock_result

        repo = SQLAlchemyProcessamentoRepository(session=mock_session)

        # Act
        result = await repo.buscar_por_analise_id(analise_id)

        # Assert
        assert result is not None
        assert result.id == sample_processamento.id
        assert result.analise_id == analise_id
        assert result.status == StatusProcessamento.PENDENTE
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_buscar_por_analise_id_not_found(self, analise_id: uuid.UUID) -> None:
        """Test buscar_por_analise_id returns None when not found."""
        # Arrange
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repo = SQLAlchemyProcessamentoRepository(session=mock_session)

        # Act
        result = await repo.buscar_por_analise_id(analise_id)

        # Assert
        assert result is None
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_salvar_processamento(self, sample_processamento: Processamento) -> None:
        """Test salvar_processamento persists a new processamento."""
        # Arrange
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        repo = SQLAlchemyProcessamentoRepository(session=mock_session)

        # Act
        result = await repo.salvar_processamento(sample_processamento)

        # Assert
        assert result.id == sample_processamento.id
        assert result.analise_id == sample_processamento.analise_id
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_atualizar_processamento(self, sample_processamento: Processamento) -> None:
        """Test atualizar_processamento updates existing processamento."""
        # Arrange
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_model = ProcessamentoModel(
            id=sample_processamento.id,
            analise_id=sample_processamento.analise_id,
            status="pendente",
            tentativas=0,
            iniciado_em=None,
            concluido_em=None,
            erro_detalhe=None,
        )
        mock_result.scalar_one.return_value = mock_model
        mock_session.execute.return_value = mock_result
        mock_session.flush = AsyncMock()

        repo = SQLAlchemyProcessamentoRepository(session=mock_session)

        # Update the processamento status
        updated_processamento = Processamento(
            id=sample_processamento.id,
            analise_id=sample_processamento.analise_id,
            status=StatusProcessamento.CONCLUIDO,
            tentativas=1,
            iniciado_em=sample_processamento.iniciado_em,
            concluido_em=sample_processamento.concluido_em,
            erro_detalhe=None,
        )

        # Act
        await repo.atualizar_processamento(updated_processamento)

        # Assert
        assert mock_model.status == StatusProcessamento.CONCLUIDO.value
        assert mock_model.tentativas == 1
        mock_session.execute.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_salvar_componentes(self, sample_componente: Componente) -> None:
        """Test salvar_componentes persists a list of componentes."""
        # Arrange
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        repo = SQLAlchemyProcessamentoRepository(session=mock_session)
        componentes = [sample_componente]

        # Act
        result = await repo.salvar_componentes(componentes)

        # Assert
        assert len(result) == 1
        assert result[0].id == sample_componente.id
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_salvar_componentes_multiple(self, processamento_id: uuid.UUID) -> None:
        """Test salvar_componentes persists multiple componentes."""
        # Arrange
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        repo = SQLAlchemyProcessamentoRepository(session=mock_session)

        componentes = [
            Componente(
                id=uuid.uuid4(),
                processamento_id=processamento_id,
                nome="API Gateway",
                tipo="api_gateway",
                confianca=0.95,
                metadata={"descricao": "API Gateway"},
            ),
            Componente(
                id=uuid.uuid4(),
                processamento_id=processamento_id,
                nome="Database",
                tipo="database",
                confianca=0.9,
                metadata={"descricao": "PostgreSQL"},
            ),
        ]

        # Act
        result = await repo.salvar_componentes(componentes)

        # Assert
        assert len(result) == 2
        assert mock_session.add.call_count == 2
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_salvar_riscos_with_valid_componentes(self, sample_risco: Risco, componente_id: uuid.UUID) -> None:
        """Test salvar_riscos persists riscos and their component relations."""
        # Arrange
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        repo = SQLAlchemyProcessamentoRepository(session=mock_session)

        mapa_componente_ids = {"API Gateway": componente_id}
        riscos = [sample_risco]

        # Act
        result = await repo.salvar_riscos(riscos, mapa_componente_ids)

        # Assert
        assert len(result) == 1
        assert result[0].id == sample_risco.id
        # add called for risco_model + risco_componente_model
        assert mock_session.add.call_count == 2
        # flush called for risco + final flush for relations
        assert mock_session.flush.call_count == 2

    @pytest.mark.asyncio
    async def test_salvar_riscos_with_missing_componente(
        self, processamento_id: uuid.UUID, risco_id: uuid.UUID
    ) -> None:
        """Test salvar_riscos skips relation when componente not in mapa."""
        # Arrange
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        repo = SQLAlchemyProcessamentoRepository(session=mock_session)

        risco = Risco(
            id=risco_id,
            processamento_id=processamento_id,
            descricao="Test risk",
            severidade="alta",
            recomendacao_descricao="Fix it",
            recomendacao_prioridade="alta",
            componentes_afetados=["NonExistentComponent"],
        )

        mapa_componente_ids = {"API Gateway": uuid.uuid4()}
        riscos = [risco]

        # Act
        result = await repo.salvar_riscos(riscos, mapa_componente_ids)

        # Assert
        assert len(result) == 1
        # add called only for risco_model (no relation added)
        assert mock_session.add.call_count == 1
        # flush called twice (after risco, and final flush)
        assert mock_session.flush.call_count == 2

    @pytest.mark.asyncio
    async def test_salvar_riscos_multiple_with_mixed_componentes(self, processamento_id: uuid.UUID) -> None:
        """Test salvar_riscos with multiple riscos and mixed componente references."""
        # Arrange
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        repo = SQLAlchemyProcessamentoRepository(session=mock_session)

        comp1_id = uuid.uuid4()
        comp2_id = uuid.uuid4()

        risco1 = Risco(
            id=uuid.uuid4(),
            processamento_id=processamento_id,
            descricao="Risk 1",
            severidade="alta",
            recomendacao_descricao="Fix 1",
            recomendacao_prioridade="alta",
            componentes_afetados=["API Gateway", "Database"],
        )

        risco2 = Risco(
            id=uuid.uuid4(),
            processamento_id=processamento_id,
            descricao="Risk 2",
            severidade="media",
            recomendacao_descricao="Fix 2",
            recomendacao_prioridade="media",
            componentes_afetados=["NonExistent"],
        )

        mapa = {"API Gateway": comp1_id, "Database": comp2_id}

        # Act
        result = await repo.salvar_riscos([risco1, risco2], mapa)

        # Assert
        assert len(result) == 2
        # 2 risk models + 2 relations from risco1 + 0 from risco2
        assert mock_session.add.call_count == 4
        assert mock_session.flush.call_count == 3

    @pytest.mark.asyncio
    async def test_buscar_resultado_completo_found(
        self,
        analise_id: uuid.UUID,
        sample_processamento: Processamento,
        sample_componente: Componente,
        sample_risco: Risco,
    ) -> None:
        """Test buscar_resultado_completo returns complete result when found."""
        # Arrange
        mock_session = AsyncMock()

        # Mock for processamento query
        mock_proc_result = MagicMock()
        mock_proc_model = ProcessamentoModel(
            id=sample_processamento.id,
            analise_id=analise_id,
            status=sample_processamento.status.value,
            tentativas=sample_processamento.tentativas,
            iniciado_em=sample_processamento.iniciado_em,
            concluido_em=sample_processamento.concluido_em,
            erro_detalhe=sample_processamento.erro_detalhe,
        )
        mock_proc_result.scalar_one_or_none.return_value = mock_proc_model

        # Mock for componentes query
        mock_comp_result = MagicMock()
        mock_comp_scalars = MagicMock()
        mock_comp_model = ComponenteModel(
            id=sample_componente.id,
            processamento_id=sample_componente.processamento_id,
            nome=sample_componente.nome,
            tipo=sample_componente.tipo,
            confianca=sample_componente.confianca,
            metadata_=sample_componente.metadata,
        )
        mock_comp_scalars.all.return_value = [mock_comp_model]
        mock_comp_result.scalars.return_value = mock_comp_scalars

        # Mock for riscos query
        mock_risco_result = MagicMock()
        mock_risco_scalars = MagicMock()
        mock_risco_model = RiscoModel(
            id=sample_risco.id,
            processamento_id=sample_risco.processamento_id,
            descricao=sample_risco.descricao,
            severidade=sample_risco.severidade,
            recomendacao_descricao=sample_risco.recomendacao_descricao,
            recomendacao_prioridade=sample_risco.recomendacao_prioridade,
        )
        mock_risco_scalars.all.return_value = [mock_risco_model]
        mock_risco_result.scalars.return_value = mock_risco_scalars

        # Mock for risco_componentes query
        mock_rel_result = MagicMock()
        mock_rel_scalars = MagicMock()
        mock_rel_model = RiscoComponenteModel(
            risco_id=sample_risco.id,
            componente_id=sample_componente.id,
        )
        mock_rel_scalars.all.return_value = [mock_rel_model]
        mock_rel_result.scalars.return_value = mock_rel_scalars

        mock_session.execute.side_effect = [
            mock_proc_result,
            mock_comp_result,
            mock_risco_result,
            mock_rel_result,
        ]

        repo = SQLAlchemyProcessamentoRepository(session=mock_session)

        # Act
        processamento, componentes, riscos = await repo.buscar_resultado_completo(analise_id)

        # Assert
        assert processamento is not None
        assert processamento.id == sample_processamento.id
        assert len(componentes) == 1
        assert componentes[0].nome == "API Gateway"
        assert len(riscos) == 1
        assert riscos[0].descricao == sample_risco.descricao
        assert riscos[0].componentes_afetados == ["API Gateway"]
        assert mock_session.execute.call_count == 4

    @pytest.mark.asyncio
    async def test_buscar_resultado_completo_not_found(self, analise_id: uuid.UUID) -> None:
        """Test buscar_resultado_completo returns empty result when not found."""
        # Arrange
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repo = SQLAlchemyProcessamentoRepository(session=mock_session)

        # Act
        processamento, componentes, riscos = await repo.buscar_resultado_completo(analise_id)

        # Assert
        assert processamento is None
        assert componentes == []
        assert riscos == []
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_buscar_resultado_completo_with_multiple_components_and_risks(self, analise_id: uuid.UUID) -> None:
        """Test buscar_resultado_completo with multiple components and risks."""
        # Arrange
        mock_session = AsyncMock()
        processamento_id = uuid.uuid4()
        comp1_id = uuid.uuid4()
        comp2_id = uuid.uuid4()
        risk1_id = uuid.uuid4()
        risk2_id = uuid.uuid4()

        # Mock processamento
        mock_proc_result = MagicMock()
        mock_proc_model = ProcessamentoModel(
            id=processamento_id,
            analise_id=analise_id,
            status="concluido",
            tentativas=1,
            iniciado_em=None,
            concluido_em=None,
            erro_detalhe=None,
        )
        mock_proc_result.scalar_one_or_none.return_value = mock_proc_model

        # Mock componentes
        mock_comp_result = MagicMock()
        mock_comp_scalars = MagicMock()
        comp1 = ComponenteModel(
            id=comp1_id,
            processamento_id=processamento_id,
            nome="API Gateway",
            tipo="api_gateway",
            confianca=0.95,
            metadata_={},
        )
        comp2 = ComponenteModel(
            id=comp2_id,
            processamento_id=processamento_id,
            nome="Database",
            tipo="database",
            confianca=0.9,
            metadata_={},
        )
        mock_comp_scalars.all.return_value = [comp1, comp2]
        mock_comp_result.scalars.return_value = mock_comp_scalars

        # Mock risks
        mock_risco_result = MagicMock()
        mock_risco_scalars = MagicMock()
        risk1 = RiscoModel(
            id=risk1_id,
            processamento_id=processamento_id,
            descricao="Risk 1",
            severidade="alta",
            recomendacao_descricao="Fix 1",
            recomendacao_prioridade="alta",
        )
        risk2 = RiscoModel(
            id=risk2_id,
            processamento_id=processamento_id,
            descricao="Risk 2",
            severidade="media",
            recomendacao_descricao="Fix 2",
            recomendacao_prioridade="media",
        )
        mock_risco_scalars.all.return_value = [risk1, risk2]
        mock_risco_result.scalars.return_value = mock_risco_scalars

        # Mock risco_componentes for risk1
        mock_rel1_result = MagicMock()
        mock_rel1_scalars = MagicMock()
        rel1 = RiscoComponenteModel(risco_id=risk1_id, componente_id=comp1_id)
        rel2 = RiscoComponenteModel(risco_id=risk1_id, componente_id=comp2_id)
        mock_rel1_scalars.all.return_value = [rel1, rel2]
        mock_rel1_result.scalars.return_value = mock_rel1_scalars

        # Mock risco_componentes for risk2
        mock_rel2_result = MagicMock()
        mock_rel2_scalars = MagicMock()
        mock_rel2_scalars.all.return_value = []
        mock_rel2_result.scalars.return_value = mock_rel2_scalars

        mock_session.execute.side_effect = [
            mock_proc_result,
            mock_comp_result,
            mock_risco_result,
            mock_rel1_result,
            mock_rel2_result,
        ]

        repo = SQLAlchemyProcessamentoRepository(session=mock_session)

        # Act
        processamento, componentes, riscos = await repo.buscar_resultado_completo(analise_id)

        # Assert
        assert processamento is not None
        assert len(componentes) == 2
        assert componentes[0].nome == "API Gateway"
        assert componentes[1].nome == "Database"
        assert len(riscos) == 2
        assert riscos[0].componentes_afetados == ["API Gateway", "Database"]
        assert riscos[1].componentes_afetados == []
        assert mock_session.execute.call_count == 5

    @pytest.mark.asyncio
    async def test_buscar_resultado_completo_with_orphaned_risco_componentes(self, analise_id: uuid.UUID) -> None:
        """Test buscar_resultado_completo filters out orphaned risco_componentes."""
        # Arrange
        mock_session = AsyncMock()
        processamento_id = uuid.uuid4()
        comp_id = uuid.uuid4()
        orphan_comp_id = uuid.uuid4()
        risk_id = uuid.uuid4()

        # Mock processamento
        mock_proc_result = MagicMock()
        mock_proc_model = ProcessamentoModel(
            id=processamento_id,
            analise_id=analise_id,
            status="concluido",
            tentativas=1,
            iniciado_em=None,
            concluido_em=None,
            erro_detalhe=None,
        )
        mock_proc_result.scalar_one_or_none.return_value = mock_proc_model

        # Mock componentes (only one)
        mock_comp_result = MagicMock()
        mock_comp_scalars = MagicMock()
        comp = ComponenteModel(
            id=comp_id,
            processamento_id=processamento_id,
            nome="API Gateway",
            tipo="api_gateway",
            confianca=0.95,
            metadata_={},
        )
        mock_comp_scalars.all.return_value = [comp]
        mock_comp_result.scalars.return_value = mock_comp_scalars

        # Mock risks
        mock_risco_result = MagicMock()
        mock_risco_scalars = MagicMock()
        risk = RiscoModel(
            id=risk_id,
            processamento_id=processamento_id,
            descricao="Risk",
            severidade="alta",
            recomendacao_descricao="Fix",
            recomendacao_prioridade="alta",
        )
        mock_risco_scalars.all.return_value = [risk]
        mock_risco_result.scalars.return_value = mock_risco_scalars

        # Mock risco_componentes with one valid and one orphaned
        mock_rel_result = MagicMock()
        mock_rel_scalars = MagicMock()
        rel_valid = RiscoComponenteModel(risco_id=risk_id, componente_id=comp_id)
        rel_orphan = RiscoComponenteModel(risco_id=risk_id, componente_id=orphan_comp_id)
        mock_rel_scalars.all.return_value = [rel_valid, rel_orphan]
        mock_rel_result.scalars.return_value = mock_rel_scalars

        mock_session.execute.side_effect = [
            mock_proc_result,
            mock_comp_result,
            mock_risco_result,
            mock_rel_result,
        ]

        repo = SQLAlchemyProcessamentoRepository(session=mock_session)

        # Act
        processamento, componentes, riscos = await repo.buscar_resultado_completo(analise_id)

        # Assert
        assert processamento is not None
        assert len(componentes) == 1
        assert len(riscos) == 1
        # Only the valid component should be in componentes_afetados
        assert riscos[0].componentes_afetados == ["API Gateway"]
