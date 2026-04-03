"""Unit tests for domain entities."""

import uuid
from datetime import UTC, datetime

from src.domain.entities import Componente, Processamento, Risco, StatusProcessamento


class TestProcessamentoEntity:
    """Tests for the Processamento domain entity."""

    def test_processamento_creation_with_default_values(self) -> None:
        """Test creating a Processamento with default values."""
        # Arrange
        analise_id = uuid.uuid4()

        # Act
        processamento = Processamento(analise_id=analise_id)

        # Assert
        assert processamento.analise_id == analise_id
        assert isinstance(processamento.id, uuid.UUID)
        assert processamento.status == StatusProcessamento.PENDENTE
        assert processamento.tentativas == 0
        assert processamento.iniciado_em is None
        assert processamento.concluido_em is None
        assert processamento.erro_detalhe is None

    def test_processamento_iniciar(self) -> None:
        """Test marking a Processamento as started."""
        # Arrange
        analise_id = uuid.uuid4()
        processamento = Processamento(analise_id=analise_id)
        before = datetime.now(UTC)

        # Act
        processamento.iniciar()

        # Assert
        after = datetime.now(UTC)
        assert processamento.status == StatusProcessamento.EXECUTANDO
        assert processamento.tentativas == 1
        assert before <= processamento.iniciado_em <= after

    def test_processamento_iniciar_increments_attempts(self) -> None:
        """Test that calling iniciar multiple times increments tentativas."""
        # Arrange
        analise_id = uuid.uuid4()
        processamento = Processamento(analise_id=analise_id)

        # Act
        processamento.iniciar()
        first_attempt = processamento.tentativas
        processamento.iniciar()
        second_attempt = processamento.tentativas

        # Assert
        assert first_attempt == 1
        assert second_attempt == 2

    def test_processamento_concluir(self) -> None:
        """Test marking a Processamento as completed."""
        # Arrange
        analise_id = uuid.uuid4()
        processamento = Processamento(analise_id=analise_id)
        before = datetime.now(UTC)

        # Act
        processamento.concluir()

        # Assert
        after = datetime.now(UTC)
        assert processamento.status == StatusProcessamento.CONCLUIDO
        assert before <= processamento.concluido_em <= after

    def test_processamento_falhar(self) -> None:
        """Test marking a Processamento as failed."""
        # Arrange
        analise_id = uuid.uuid4()
        processamento = Processamento(analise_id=analise_id)
        erro = "Connection timeout"
        before = datetime.now(UTC)

        # Act
        processamento.falhar(erro)

        # Assert
        after = datetime.now(UTC)
        assert processamento.status == StatusProcessamento.ERRO
        assert processamento.erro_detalhe == erro
        assert before <= processamento.concluido_em <= after

    def test_processamento_lifecycle(self) -> None:
        """Test complete lifecycle: pendente -> executando -> concluido."""
        # Arrange
        analise_id = uuid.uuid4()
        processamento = Processamento(analise_id=analise_id)

        # Act & Assert - Initial state
        assert processamento.status == StatusProcessamento.PENDENTE

        # Act - Start
        processamento.iniciar()
        assert processamento.status == StatusProcessamento.EXECUTANDO
        assert processamento.tentativas == 1

        # Act - Complete
        processamento.concluir()
        assert processamento.status == StatusProcessamento.CONCLUIDO
        assert processamento.iniciado_em is not None
        assert processamento.concluido_em is not None

    def test_processamento_with_explicit_id(self) -> None:
        """Test creating a Processamento with explicit id."""
        # Arrange
        processamento_id = uuid.uuid4()
        analise_id = uuid.uuid4()

        # Act
        processamento = Processamento(id=processamento_id, analise_id=analise_id)

        # Assert
        assert processamento.id == processamento_id


class TestComponenteEntity:
    """Tests for the Componente domain entity."""

    def test_componente_creation_with_defaults(self) -> None:
        """Test creating a Componente with default values."""
        # Arrange
        processamento_id = uuid.uuid4()

        # Act
        componente = Componente(
            processamento_id=processamento_id,
            nome="API Gateway",
            tipo="api_gateway",
        )

        # Assert
        assert isinstance(componente.id, uuid.UUID)
        assert componente.processamento_id == processamento_id
        assert componente.nome == "API Gateway"
        assert componente.tipo == "api_gateway"
        assert componente.confianca == 0.0
        assert componente.metadata == {}

    def test_componente_creation_with_all_fields(self) -> None:
        """Test creating a Componente with all fields."""
        # Arrange
        componente_id = uuid.uuid4()
        processamento_id = uuid.uuid4()
        metadata = {"descricao": "Main API Gateway"}

        # Act
        componente = Componente(
            id=componente_id,
            processamento_id=processamento_id,
            nome="API Gateway",
            tipo="api_gateway",
            confianca=0.95,
            metadata=metadata,
        )

        # Assert
        assert componente.id == componente_id
        assert componente.processamento_id == processamento_id
        assert componente.nome == "API Gateway"
        assert componente.tipo == "api_gateway"
        assert componente.confianca == 0.95
        assert componente.metadata == metadata

    def test_componente_confianca_range(self) -> None:
        """Test Componente with various confianca values."""
        # Arrange
        processamento_id = uuid.uuid4()

        # Act & Assert - Valid values
        for confianca in [0.0, 0.5, 0.99, 1.0]:
            componente = Componente(
                processamento_id=processamento_id,
                nome="Service",
                tipo="service",
                confianca=confianca,
            )
            assert componente.confianca == confianca

    def test_componente_types(self) -> None:
        """Test Componente with different component types."""
        # Arrange
        processamento_id = uuid.uuid4()
        tipos = ["api_gateway", "database", "queue", "service", "load_balancer", "cache", "storage", "other"]

        # Act & Assert
        for tipo in tipos:
            componente = Componente(
                processamento_id=processamento_id,
                nome="Test Component",
                tipo=tipo,
            )
            assert componente.tipo == tipo


class TestRiscoEntity:
    """Tests for the Risco domain entity."""

    def test_risco_creation_with_defaults(self) -> None:
        """Test creating a Risco with default values."""
        # Arrange
        processamento_id = uuid.uuid4()

        # Act
        risco = Risco(
            processamento_id=processamento_id,
            descricao="Single point of failure",
            severidade="alta",
        )

        # Assert
        assert isinstance(risco.id, uuid.UUID)
        assert risco.processamento_id == processamento_id
        assert risco.descricao == "Single point of failure"
        assert risco.severidade == "alta"
        assert risco.recomendacao_descricao is None
        assert risco.recomendacao_prioridade is None
        assert risco.componentes_afetados == []

    def test_risco_creation_with_all_fields(self) -> None:
        """Test creating a Risco with all fields."""
        # Arrange
        risco_id = uuid.uuid4()
        processamento_id = uuid.uuid4()
        componentes_afetados = ["API Gateway", "Database"]

        # Act
        risco = Risco(
            id=risco_id,
            processamento_id=processamento_id,
            descricao="Lack of redundancy",
            severidade="critica",
            recomendacao_descricao="Implement multi-region deployment",
            recomendacao_prioridade="critica",
            componentes_afetados=componentes_afetados,
        )

        # Assert
        assert risco.id == risco_id
        assert risco.processamento_id == processamento_id
        assert risco.descricao == "Lack of redundancy"
        assert risco.severidade == "critica"
        assert risco.recomendacao_descricao == "Implement multi-region deployment"
        assert risco.recomendacao_prioridade == "critica"
        assert risco.componentes_afetados == componentes_afetados

    def test_risco_severidades(self) -> None:
        """Test Risco with different severity levels."""
        # Arrange
        processamento_id = uuid.uuid4()
        severidades = ["baixa", "media", "alta", "critica"]

        # Act & Assert
        for severidade in severidades:
            risco = Risco(
                processamento_id=processamento_id,
                descricao="Test risk",
                severidade=severidade,
            )
            assert risco.severidade == severidade

    def test_risco_with_multiple_affected_components(self) -> None:
        """Test Risco with multiple affected components."""
        # Arrange
        processamento_id = uuid.uuid4()
        componentes = ["API Gateway", "Service A", "Service B", "Database"]

        # Act
        risco = Risco(
            processamento_id=processamento_id,
            descricao="Network latency affecting multiple services",
            severidade="media",
            componentes_afetados=componentes,
        )

        # Assert
        assert len(risco.componentes_afetados) == 4
        assert risco.componentes_afetados == componentes

    def test_risco_with_explicit_id(self) -> None:
        """Test creating a Risco with explicit id."""
        # Arrange
        risco_id = uuid.uuid4()
        processamento_id = uuid.uuid4()

        # Act
        risco = Risco(
            id=risco_id,
            processamento_id=processamento_id,
            descricao="Test risk",
            severidade="media",
        )

        # Assert
        assert risco.id == risco_id
