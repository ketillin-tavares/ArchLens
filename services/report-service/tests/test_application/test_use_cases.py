"""Unit tests for application use cases."""

import uuid
from typing import Any
from unittest.mock import AsyncMock

import pytest

from src.application.use_cases import GenerateReport, GetReport
from src.domain.entities import Relatorio
from src.domain.exceptions import RelatorioNaoEncontradoError
from src.domain.repositories import RelatorioRepository


class TestGenerateReport:
    """Tests for the GenerateReport use case."""

    async def test_generate_report_creates_new_relatorio(
        self, mock_relatorio_repository: RelatorioRepository, mock_event_publisher: Any
    ) -> None:
        """Test that GenerateReport creates and persists a new relatório."""
        # Arrange
        analise_id = uuid.uuid4()
        componentes = [
            {"id": "1", "nome": "API Gateway"},
            {"id": "2", "nome": "Database"},
        ]
        riscos = [
            {"id": "1", "severidade": "alta", "descricao": "Issue"},
        ]

        mock_relatorio_repository.existe_por_analise_id.return_value = False
        mock_relatorio_repository.salvar.return_value = Relatorio(
            id=uuid.uuid4(),
            analise_id=analise_id,
            titulo="Test Title",
            resumo="Test Summary",
            conteudo={},
        )

        use_case = GenerateReport(
            relatorio_repository=mock_relatorio_repository,
            event_publisher=mock_event_publisher,
        )

        # Act
        await use_case.execute(str(analise_id), componentes, riscos)

        # Assert
        mock_relatorio_repository.existe_por_analise_id.assert_called_once()
        mock_relatorio_repository.salvar.assert_called_once()
        mock_event_publisher.publish_event.assert_called_once()

    async def test_generate_report_skips_duplicate_relatorio(
        self, mock_relatorio_repository: RelatorioRepository, mock_event_publisher: Any
    ) -> None:
        """Test that GenerateReport skips if relatório already exists (idempotency)."""
        # Arrange
        analise_id = uuid.uuid4()
        componentes = [{"id": "1", "nome": "API"}]
        riscos = [{"id": "1", "severidade": "alta"}]

        mock_relatorio_repository.existe_por_analise_id.return_value = True

        use_case = GenerateReport(
            relatorio_repository=mock_relatorio_repository,
            event_publisher=mock_event_publisher,
        )

        # Act
        await use_case.execute(str(analise_id), componentes, riscos)

        # Assert
        mock_relatorio_repository.existe_por_analise_id.assert_called_once()
        mock_relatorio_repository.salvar.assert_not_called()
        mock_event_publisher.publish_event.assert_not_called()

    async def test_generate_report_calculates_statistics_correctly(
        self, mock_relatorio_repository: RelatorioRepository, mock_event_publisher: Any
    ) -> None:
        """Test that GenerateReport calculates statistics correctly."""
        # Arrange
        analise_id = uuid.uuid4()
        componentes = [
            {"id": "1", "nome": "API"},
            {"id": "2", "nome": "DB"},
            {"id": "3", "nome": "Cache"},
        ]
        riscos = [
            {"id": "1", "severidade": "critica"},
            {"id": "2", "severidade": "alta"},
            {"id": "3", "severidade": "alta"},
            {"id": "4", "severidade": "media"},
        ]

        mock_relatorio_repository.existe_por_analise_id.return_value = False
        saved_relatorio = None

        async def capture_relatorio(rel: Relatorio) -> Relatorio:
            nonlocal saved_relatorio
            saved_relatorio = rel
            return rel

        mock_relatorio_repository.salvar.side_effect = capture_relatorio

        use_case = GenerateReport(
            relatorio_repository=mock_relatorio_repository,
            event_publisher=mock_event_publisher,
        )

        # Act
        await use_case.execute(str(analise_id), componentes, riscos)

        # Assert
        assert saved_relatorio is not None
        stats = saved_relatorio.conteudo["estatisticas"]
        assert stats["total_componentes"] == 3
        assert stats["total_riscos"] == 4
        assert stats["riscos_por_severidade"]["critica"] == 1
        assert stats["riscos_por_severidade"]["alta"] == 2
        assert stats["riscos_por_severidade"]["media"] == 1
        assert stats["riscos_por_severidade"]["baixa"] == 0

    async def test_generate_report_with_zero_riscos(
        self, mock_relatorio_repository: RelatorioRepository, mock_event_publisher: Any
    ) -> None:
        """Test GenerateReport with no riscos."""
        # Arrange
        analise_id = uuid.uuid4()
        componentes = [{"id": "1", "nome": "API"}]
        riscos = []

        mock_relatorio_repository.existe_por_analise_id.return_value = False
        saved_relatorio = None

        async def capture_relatorio(rel: Relatorio) -> Relatorio:
            nonlocal saved_relatorio
            saved_relatorio = rel
            return rel

        mock_relatorio_repository.salvar.side_effect = capture_relatorio

        use_case = GenerateReport(
            relatorio_repository=mock_relatorio_repository,
            event_publisher=mock_event_publisher,
        )

        # Act
        await use_case.execute(str(analise_id), componentes, riscos)

        # Assert
        assert saved_relatorio is not None
        stats = saved_relatorio.conteudo["estatisticas"]
        assert stats["total_riscos"] == 0
        assert all(v == 0 for v in stats["riscos_por_severidade"].values())

    async def test_generate_report_with_mixed_severidades(
        self, mock_relatorio_repository: RelatorioRepository, mock_event_publisher: Any
    ) -> None:
        """Test GenerateReport with all severity levels."""
        # Arrange
        analise_id = uuid.uuid4()
        componentes = [{"id": "1", "nome": "API"}]
        riscos = [
            {"id": "1", "severidade": "critica"},
            {"id": "2", "severidade": "alta"},
            {"id": "3", "severidade": "media"},
            {"id": "4", "severidade": "baixa"},
        ]

        mock_relatorio_repository.existe_por_analise_id.return_value = False
        saved_relatorio = None

        async def capture_relatorio(rel: Relatorio) -> Relatorio:
            nonlocal saved_relatorio
            saved_relatorio = rel
            return rel

        mock_relatorio_repository.salvar.side_effect = capture_relatorio

        use_case = GenerateReport(
            relatorio_repository=mock_relatorio_repository,
            event_publisher=mock_event_publisher,
        )

        # Act
        await use_case.execute(str(analise_id), componentes, riscos)

        # Assert
        assert saved_relatorio is not None
        stats = saved_relatorio.conteudo["estatisticas"]
        assert stats["riscos_por_severidade"]["critica"] == 1
        assert stats["riscos_por_severidade"]["alta"] == 1
        assert stats["riscos_por_severidade"]["media"] == 1
        assert stats["riscos_por_severidade"]["baixa"] == 1

    async def test_generate_report_titulo_contains_date(
        self, mock_relatorio_repository: RelatorioRepository, mock_event_publisher: Any
    ) -> None:
        """Test that generated title contains current date."""
        # Arrange
        analise_id = uuid.uuid4()
        componentes = [{"id": "1", "nome": "API"}]
        riscos = []

        mock_relatorio_repository.existe_por_analise_id.return_value = False
        saved_relatorio = None

        async def capture_relatorio(rel: Relatorio) -> Relatorio:
            nonlocal saved_relatorio
            saved_relatorio = rel
            return rel

        mock_relatorio_repository.salvar.side_effect = capture_relatorio

        use_case = GenerateReport(
            relatorio_repository=mock_relatorio_repository,
            event_publisher=mock_event_publisher,
        )

        # Act
        await use_case.execute(str(analise_id), componentes, riscos)

        # Assert
        assert saved_relatorio is not None
        assert "Análise Arquitetural" in saved_relatorio.titulo
        assert "202" in saved_relatorio.titulo  # Year 2026

    async def test_generate_report_publishes_event(
        self, mock_relatorio_repository: RelatorioRepository, mock_event_publisher: Any
    ) -> None:
        """Test that GenerateReport publishes RelatorioGerado event."""
        # Arrange
        analise_id = uuid.uuid4()
        componentes = [{"id": "1", "nome": "API"}]
        riscos = []

        relatorio_id = uuid.uuid4()
        mock_relatorio_repository.existe_por_analise_id.return_value = False
        mock_relatorio_repository.salvar.return_value = Relatorio(
            id=relatorio_id,
            analise_id=analise_id,
            titulo="Title",
            resumo="Summary",
            conteudo={},
        )

        use_case = GenerateReport(
            relatorio_repository=mock_relatorio_repository,
            event_publisher=mock_event_publisher,
        )

        # Act
        await use_case.execute(str(analise_id), componentes, riscos)

        # Assert
        mock_event_publisher.publish_event.assert_called_once()
        call_args = mock_event_publisher.publish_event.call_args
        assert call_args[1]["event_type"] == "RelatorioGerado"
        assert call_args[1]["routing_key"] == "analise.relatorio.gerado"


class TestGetReport:
    """Tests for the GetReport use case."""

    async def test_get_report_returns_relatorio_response(
        self, analise_id: uuid.UUID, sample_relatorio: Relatorio
    ) -> None:
        """Test that GetReport returns a RelatorioResponse."""
        # Arrange
        mock_repo = AsyncMock(spec=RelatorioRepository)
        mock_repo.buscar_por_analise_id.return_value = sample_relatorio

        use_case = GetReport(relatorio_repository=mock_repo)

        # Act
        response = await use_case.execute(analise_id)

        # Assert
        assert response.id == sample_relatorio.id
        assert response.analise_id == sample_relatorio.analise_id
        assert response.titulo == sample_relatorio.titulo
        assert response.resumo == sample_relatorio.resumo
        assert response.conteudo == sample_relatorio.conteudo

    async def test_get_report_raises_when_not_found(self, analise_id: uuid.UUID) -> None:
        """Test that GetReport raises RelatorioNaoEncontradoError when not found."""
        # Arrange
        mock_repo = AsyncMock(spec=RelatorioRepository)
        mock_repo.buscar_por_analise_id.return_value = None

        use_case = GetReport(relatorio_repository=mock_repo)

        # Act & Assert
        with pytest.raises(RelatorioNaoEncontradoError):
            await use_case.execute(analise_id)

    async def test_get_report_calls_repository(self, analise_id: uuid.UUID, sample_relatorio: Relatorio) -> None:
        """Test that GetReport calls the repository with correct analise_id."""
        # Arrange
        mock_repo = AsyncMock(spec=RelatorioRepository)
        mock_repo.buscar_por_analise_id.return_value = sample_relatorio

        use_case = GetReport(relatorio_repository=mock_repo)

        # Act
        await use_case.execute(analise_id)

        # Assert
        mock_repo.buscar_por_analise_id.assert_called_once_with(analise_id)
