"""Unit tests for domain entities."""

import uuid
from datetime import UTC, datetime

import pytest

from src.domain.entities import Relatorio


class TestRelatorioEntity:
    """Tests for the Relatorio domain entity."""

    def test_relatorio_creation_with_valid_data(self) -> None:
        """Test creating a Relatorio with valid data."""
        # Arrange
        analise_id = uuid.uuid4()
        titulo = "Análise Arquitetural - 2026-04-01"
        resumo = "Foram identificados 5 componentes e 3 riscos."
        conteudo = {
            "componentes": [{"id": "1", "nome": "API"}],
            "riscos": [{"id": "1", "severidade": "critica"}],
        }

        # Act
        relatorio = Relatorio(
            analise_id=analise_id,
            titulo=titulo,
            resumo=resumo,
            conteudo=conteudo,
        )

        # Assert
        assert relatorio.analise_id == analise_id
        assert relatorio.titulo == titulo
        assert relatorio.resumo == resumo
        assert relatorio.conteudo == conteudo
        assert isinstance(relatorio.id, uuid.UUID)
        assert isinstance(relatorio.criado_em, datetime)

    def test_relatorio_generates_default_id(self) -> None:
        """Test that Relatorio generates a default UUID for id."""
        # Arrange
        analise_id = uuid.uuid4()

        # Act
        relatorio1 = Relatorio(
            analise_id=analise_id,
            titulo="Title",
            resumo="Summary",
            conteudo={},
        )
        relatorio2 = Relatorio(
            analise_id=analise_id,
            titulo="Title",
            resumo="Summary",
            conteudo={},
        )

        # Assert
        assert isinstance(relatorio1.id, uuid.UUID)
        assert isinstance(relatorio2.id, uuid.UUID)
        assert relatorio1.id != relatorio2.id

    def test_relatorio_generates_default_criado_em(self) -> None:
        """Test that Relatorio generates a default timestamp for criado_em."""
        # Arrange
        before = datetime.now(UTC)
        analise_id = uuid.uuid4()

        # Act
        relatorio = Relatorio(
            analise_id=analise_id,
            titulo="Title",
            resumo="Summary",
            conteudo={},
        )

        after = datetime.now(UTC)

        # Assert
        assert before <= relatorio.criado_em <= after

    def test_relatorio_with_custom_id_and_timestamp(self) -> None:
        """Test creating a Relatorio with explicit id and criado_em."""
        # Arrange
        relatorio_id = uuid.uuid4()
        analise_id = uuid.uuid4()
        custom_timestamp = datetime(2026, 4, 1, 12, 0, 0, tzinfo=UTC)

        # Act
        relatorio = Relatorio(
            id=relatorio_id,
            analise_id=analise_id,
            titulo="Title",
            resumo="Summary",
            conteudo={},
            criado_em=custom_timestamp,
        )

        # Assert
        assert relatorio.id == relatorio_id
        assert relatorio.criado_em == custom_timestamp

    def test_relatorio_conteudo_accepts_complex_dict(self) -> None:
        """Test that conteudo accepts complex nested dictionaries."""
        # Arrange
        analise_id = uuid.uuid4()
        conteudo = {
            "componentes": [
                {"id": "1", "nome": "API", "dependencias": ["DB", "Cache"]},
                {"id": "2", "nome": "DB", "config": {"host": "localhost", "port": 5432}},
            ],
            "riscos": [
                {
                    "id": "1",
                    "severidade": "critica",
                    "impacto": {"performance": 0.8, "security": 0.9},
                }
            ],
            "estatisticas": {
                "total_componentes": 2,
                "total_riscos": 1,
                "riscos_por_severidade": {"critica": 1, "alta": 0, "media": 0, "baixa": 0},
            },
        }

        # Act
        relatorio = Relatorio(
            analise_id=analise_id,
            titulo="Title",
            resumo="Summary",
            conteudo=conteudo,
        )

        # Assert
        assert relatorio.conteudo == conteudo
        assert len(relatorio.conteudo["componentes"]) == 2
        assert relatorio.conteudo["estatisticas"]["total_componentes"] == 2

    def test_relatorio_pydantic_validation(self) -> None:
        """Test that Relatorio validates required fields using Pydantic."""
        # Arrange & Act & Assert
        with pytest.raises(ValueError):
            Relatorio(
                analise_id=uuid.uuid4(),
                # Missing titulo (required)
                resumo="Summary",
                conteudo={},
            )

        with pytest.raises(ValueError):
            Relatorio(
                analise_id=uuid.uuid4(),
                titulo="Title",
                # Missing resumo (required)
                conteudo={},
            )

        with pytest.raises(ValueError):
            Relatorio(
                # Missing analise_id (required)
                titulo="Title",
                resumo="Summary",
                conteudo={},
            )
