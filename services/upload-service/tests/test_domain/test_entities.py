"""Tests for domain entities."""

import uuid
from datetime import UTC, datetime

from src.domain.entities import Analise, Diagrama
from src.domain.value_objects import StatusAnalise


class TestDiagrama:
    """Tests for Diagrama entity."""

    def test_create_diagrama_with_defaults(self) -> None:
        """Test creating a Diagrama with default values."""
        # Arrange & Act
        diagrama = Diagrama(
            nome_original="arquitetura.png",
            content_type="image/png",
            tamanho_bytes=1024,
            storage_path="diagramas/2026/03/30/uuid-here.png",
        )

        # Assert
        assert diagrama.nome_original == "arquitetura.png"
        assert diagrama.content_type == "image/png"
        assert diagrama.tamanho_bytes == 1024
        assert diagrama.storage_path == "diagramas/2026/03/30/uuid-here.png"
        assert diagrama.id is not None
        assert isinstance(diagrama.id, uuid.UUID)
        assert diagrama.criado_em is not None
        assert isinstance(diagrama.criado_em, datetime)

    def test_create_diagrama_with_explicit_id(self) -> None:
        """Test creating a Diagrama with explicit ID."""
        # Arrange
        diagrama_id = uuid.uuid4()

        # Act
        diagrama = Diagrama(
            id=diagrama_id,
            nome_original="arquitetura.png",
            content_type="image/png",
            tamanho_bytes=1024,
            storage_path="diagramas/2026/03/30/uuid-here.png",
        )

        # Assert
        assert diagrama.id == diagrama_id

    def test_create_diagrama_with_explicit_timestamp(self) -> None:
        """Test creating a Diagrama with explicit creation timestamp."""
        # Arrange
        criado_em = datetime(2026, 1, 15, 10, 30, 45, tzinfo=UTC)

        # Act
        diagrama = Diagrama(
            nome_original="arquitetura.png",
            content_type="image/png",
            tamanho_bytes=1024,
            storage_path="diagramas/2026/03/30/uuid-here.png",
            criado_em=criado_em,
        )

        # Assert
        assert diagrama.criado_em == criado_em


class TestAnalise:
    """Tests for Analise entity and status transitions."""

    def test_create_analise_with_defaults(self) -> None:
        """Test creating an Analise with default values."""
        # Arrange
        diagrama_id = uuid.uuid4()

        # Act
        analise = Analise(diagrama_id=diagrama_id)

        # Assert
        assert analise.id is not None
        assert isinstance(analise.id, uuid.UUID)
        assert analise.diagrama_id == diagrama_id
        assert analise.status == StatusAnalise.RECEBIDO
        assert analise.erro_detalhe is None
        assert analise.criado_em is not None
        assert analise.atualizado_em is not None

    def test_create_analise_with_explicit_status(self) -> None:
        """Test creating an Analise with explicit status."""
        # Arrange
        diagrama_id = uuid.uuid4()

        # Act
        analise = Analise(
            diagrama_id=diagrama_id,
            status=StatusAnalise.EM_PROCESSAMENTO,
        )

        # Assert
        assert analise.status == StatusAnalise.EM_PROCESSAMENTO

    def test_atualizar_status_valid_transition(self) -> None:
        """Test valid status transition."""
        # Arrange
        analise = Analise(
            diagrama_id=uuid.uuid4(),
            status=StatusAnalise.RECEBIDO,
        )
        original_atualizado_em = analise.atualizado_em

        # Act
        result = analise.atualizar_status(StatusAnalise.EM_PROCESSAMENTO)

        # Assert
        assert result is True
        assert analise.status == StatusAnalise.EM_PROCESSAMENTO
        assert analise.atualizado_em > original_atualizado_em

    def test_atualizar_status_multiple_transitions(self) -> None:
        """Test multiple valid status transitions in sequence."""
        # Arrange
        analise = Analise(
            diagrama_id=uuid.uuid4(),
            status=StatusAnalise.RECEBIDO,
        )

        # Act & Assert
        assert analise.atualizar_status(StatusAnalise.EM_PROCESSAMENTO) is True
        assert analise.status == StatusAnalise.EM_PROCESSAMENTO

        assert analise.atualizar_status(StatusAnalise.ANALISADO) is True
        assert analise.status == StatusAnalise.ANALISADO

    def test_atualizar_status_rejects_regression(self) -> None:
        """Test that regressing to earlier status is rejected."""
        # Arrange
        analise = Analise(
            diagrama_id=uuid.uuid4(),
            status=StatusAnalise.ANALISADO,
        )
        original_status = analise.status

        # Act
        result = analise.atualizar_status(StatusAnalise.EM_PROCESSAMENTO)

        # Assert
        assert result is False
        assert analise.status == original_status

    def test_atualizar_status_rejects_same_status(self) -> None:
        """Test that updating to same status is rejected."""
        # Arrange
        analise = Analise(
            diagrama_id=uuid.uuid4(),
            status=StatusAnalise.RECEBIDO,
        )
        original_atualizado_em = analise.atualizado_em

        # Act
        result = analise.atualizar_status(StatusAnalise.RECEBIDO)

        # Assert
        assert result is False
        assert analise.status == StatusAnalise.RECEBIDO
        assert analise.atualizado_em == original_atualizado_em

    def test_atualizar_status_to_erro_with_details(self) -> None:
        """Test updating to ERRO status with error details."""
        # Arrange
        analise = Analise(
            diagrama_id=uuid.uuid4(),
            status=StatusAnalise.EM_PROCESSAMENTO,
        )

        # Act
        erro_msg = "Diagrama possui estrutura inválida"
        result = analise.atualizar_status(StatusAnalise.ERRO, erro_detalhe=erro_msg)

        # Assert
        assert result is True
        assert analise.status == StatusAnalise.ERRO
        assert analise.erro_detalhe == erro_msg

    def test_atualizar_status_to_erro_without_details(self) -> None:
        """Test updating to ERRO status without error details."""
        # Arrange
        analise = Analise(
            diagrama_id=uuid.uuid4(),
            status=StatusAnalise.EM_PROCESSAMENTO,
        )

        # Act
        result = analise.atualizar_status(StatusAnalise.ERRO)

        # Assert
        assert result is True
        assert analise.status == StatusAnalise.ERRO
        assert analise.erro_detalhe is None

    def test_atualizar_status_preserves_existing_error_details(self) -> None:
        """Test that existing error details are preserved if not overwritten."""
        # Arrange
        erro_original = "Erro original"
        analise = Analise(
            diagrama_id=uuid.uuid4(),
            status=StatusAnalise.EM_PROCESSAMENTO,
            erro_detalhe=erro_original,
        )

        # Act
        result = analise.atualizar_status(StatusAnalise.ERRO)

        # Assert
        assert result is True
        assert analise.erro_detalhe == erro_original

    def test_atualizar_status_from_recebido_to_erro_allowed(self) -> None:
        """Test that ERRO status can be reached from RECEBIDO (fast path)."""
        # Arrange
        analise = Analise(
            diagrama_id=uuid.uuid4(),
            status=StatusAnalise.RECEBIDO,
        )

        # Act
        result = analise.atualizar_status(StatusAnalise.ERRO, erro_detalhe="Quick error")

        # Assert
        assert result is True
        assert analise.status == StatusAnalise.ERRO
        assert analise.erro_detalhe == "Quick error"

    def test_atualizar_status_idempotent_skip(self) -> None:
        """Test idempotent behavior when transition is invalid."""
        # Arrange
        analise = Analise(
            diagrama_id=uuid.uuid4(),
            status=StatusAnalise.ANALISADO,
        )
        original_timestamp = analise.atualizado_em

        # Act - Try to regress multiple times
        result1 = analise.atualizar_status(StatusAnalise.EM_PROCESSAMENTO)
        result2 = analise.atualizar_status(StatusAnalise.EM_PROCESSAMENTO)

        # Assert
        assert result1 is False
        assert result2 is False
        assert analise.status == StatusAnalise.ANALISADO
        assert analise.atualizado_em == original_timestamp
