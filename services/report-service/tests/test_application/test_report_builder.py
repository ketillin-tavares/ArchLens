"""Unit tests for report builder helper methods."""

from typing import Any

from src.application.use_cases.generate_report import GenerateReport


class TestCalcularEstatisticas:
    """Tests for the _calcular_estatisticas static method."""

    def test_calculate_statistics_with_no_riscos(self) -> None:
        """Test statistics calculation with no riscos."""
        # Arrange
        componentes = [{"id": "1", "nome": "API"}]
        riscos: list[dict[str, Any]] = []

        # Act
        stats = GenerateReport._calcular_estatisticas(componentes, riscos)

        # Assert
        assert stats["total_componentes"] == 1
        assert stats["total_riscos"] == 0
        assert stats["riscos_por_severidade"]["critica"] == 0
        assert stats["riscos_por_severidade"]["alta"] == 0
        assert stats["riscos_por_severidade"]["media"] == 0
        assert stats["riscos_por_severidade"]["baixa"] == 0

    def test_calculate_statistics_with_all_severidades(self) -> None:
        """Test statistics with all severity levels present."""
        # Arrange
        componentes = [{"id": "1", "nome": "API"}]
        riscos = [
            {"id": "1", "severidade": "critica"},
            {"id": "2", "severidade": "alta"},
            {"id": "3", "severidade": "media"},
            {"id": "4", "severidade": "baixa"},
        ]

        # Act
        stats = GenerateReport._calcular_estatisticas(componentes, riscos)

        # Assert
        assert stats["total_riscos"] == 4
        assert stats["riscos_por_severidade"]["critica"] == 1
        assert stats["riscos_por_severidade"]["alta"] == 1
        assert stats["riscos_por_severidade"]["media"] == 1
        assert stats["riscos_por_severidade"]["baixa"] == 1

    def test_calculate_statistics_with_repeated_severidades(self) -> None:
        """Test statistics with multiple riscos of same severity."""
        # Arrange
        componentes = [{"id": "1", "nome": "API"}, {"id": "2", "nome": "DB"}]
        riscos = [
            {"id": "1", "severidade": "alta"},
            {"id": "2", "severidade": "alta"},
            {"id": "3", "severidade": "alta"},
            {"id": "4", "severidade": "media"},
            {"id": "5", "severidade": "media"},
        ]

        # Act
        stats = GenerateReport._calcular_estatisticas(componentes, riscos)

        # Assert
        assert stats["total_componentes"] == 2
        assert stats["total_riscos"] == 5
        assert stats["riscos_por_severidade"]["alta"] == 3
        assert stats["riscos_por_severidade"]["media"] == 2
        assert stats["riscos_por_severidade"]["critica"] == 0
        assert stats["riscos_por_severidade"]["baixa"] == 0

    def test_calculate_statistics_ignores_unknown_severidade(self) -> None:
        """Test that unknown severidade levels are ignored."""
        # Arrange
        componentes = [{"id": "1", "nome": "API"}]
        riscos = [
            {"id": "1", "severidade": "critica"},
            {"id": "2", "severidade": "unknown"},
            {"id": "3", "severidade": "ALTA"},  # Gets converted to lowercase
            {"id": "4", "severidade": "alta"},
        ]

        # Act
        stats = GenerateReport._calcular_estatisticas(componentes, riscos)

        # Assert
        assert stats["total_riscos"] == 4  # All riscos are counted
        assert stats["riscos_por_severidade"]["critica"] == 1
        assert stats["riscos_por_severidade"]["alta"] == 2  # Both "ALTA" and "alta" match after lowercasing
        assert stats["riscos_por_severidade"]["media"] == 0
        assert stats["riscos_por_severidade"]["baixa"] == 0

    def test_calculate_statistics_with_risco_missing_severidade(self) -> None:
        """Test that riscos without severidade field are ignored."""
        # Arrange
        componentes = [{"id": "1", "nome": "API"}]
        riscos = [
            {"id": "1", "severidade": "alta"},
            {"id": "2", "descricao": "No severidade field"},
            {"id": "3", "severidade": "media"},
        ]

        # Act
        stats = GenerateReport._calcular_estatisticas(componentes, riscos)

        # Assert
        assert stats["total_riscos"] == 3  # All are counted in total
        assert stats["riscos_por_severidade"]["alta"] == 1
        assert stats["riscos_por_severidade"]["media"] == 1


class TestGerarResumo:
    """Tests for the _gerar_resumo static method."""

    def test_gerar_resumo_with_no_riscos(self) -> None:
        """Test resumo generation with no riscos."""
        # Arrange
        stats = {
            "total_componentes": 5,
            "total_riscos": 0,
            "riscos_por_severidade": {"critica": 0, "alta": 0, "media": 0, "baixa": 0},
        }

        # Act
        resumo = GenerateReport._gerar_resumo(stats)

        # Assert
        assert "5 componentes" in resumo
        assert "0 riscos" in resumo
        assert "crítico" not in resumo

    def test_gerar_resumo_with_single_risco_each_severity(self) -> None:
        """Test resumo with one risco of each severity."""
        # Arrange
        stats = {
            "total_componentes": 3,
            "total_riscos": 4,
            "riscos_por_severidade": {"critica": 1, "alta": 1, "media": 1, "baixa": 1},
        }

        # Act
        resumo = GenerateReport._gerar_resumo(stats)

        # Assert
        assert "3 componentes" in resumo
        assert "4 riscos" in resumo
        assert "1 crítico(s)" in resumo
        assert "1 alto(s)" in resumo
        assert "1 médio(s)" in resumo
        assert "1 baixo(s)" in resumo

    def test_gerar_resumo_with_multiple_riscos_high_severity(self) -> None:
        """Test resumo with multiple critical and high severity riscos."""
        # Arrange
        stats = {
            "total_componentes": 10,
            "total_riscos": 5,
            "riscos_por_severidade": {"critica": 2, "alta": 3, "media": 0, "baixa": 0},
        }

        # Act
        resumo = GenerateReport._gerar_resumo(stats)

        # Assert
        assert "10 componentes" in resumo
        assert "5 riscos" in resumo
        assert "2 crítico(s)" in resumo
        assert "3 alto(s)" in resumo
        assert "médio" not in resumo
        assert "baixo" not in resumo

    def test_gerar_resumo_zero_componentes(self) -> None:
        """Test resumo with zero componentes."""
        # Arrange
        stats = {
            "total_componentes": 0,
            "total_riscos": 1,
            "riscos_por_severidade": {"critica": 1, "alta": 0, "media": 0, "baixa": 0},
        }

        # Act
        resumo = GenerateReport._gerar_resumo(stats)

        # Assert
        assert "0 componentes" in resumo
        assert "1 riscos" in resumo
        assert "1 crítico(s)" in resumo

    def test_gerar_resumo_only_baixa_severidade(self) -> None:
        """Test resumo with only low severity riscos."""
        # Arrange
        stats = {
            "total_componentes": 8,
            "total_riscos": 2,
            "riscos_por_severidade": {"critica": 0, "alta": 0, "media": 0, "baixa": 2},
        }

        # Act
        resumo = GenerateReport._gerar_resumo(stats)

        # Assert
        assert "8 componentes" in resumo
        assert "2 riscos" in resumo
        assert "2 baixo(s)" in resumo
        assert "crítico" not in resumo
        assert "alto" not in resumo
        assert "médio" not in resumo

    def test_gerar_resumo_no_severeities_list_formatting(self) -> None:
        """Test that resumo handles empty severidade list correctly."""
        # Arrange
        stats = {
            "total_componentes": 0,
            "total_riscos": 0,
            "riscos_por_severidade": {"critica": 0, "alta": 0, "media": 0, "baixa": 0},
        }

        # Act
        resumo = GenerateReport._gerar_resumo(stats)

        # Assert
        assert "0 componentes" in resumo
        assert "0 riscos" in resumo
        assert ")" not in resumo  # No parentheses when no severidades


class TestGerarTitulo:
    """Tests for the _gerar_titulo static method."""

    def test_gerar_titulo_format(self) -> None:
        """Test that titulo has correct format."""
        # Arrange & Act
        titulo = GenerateReport._gerar_titulo()

        # Assert
        assert "Análise Arquitetural" in titulo
        assert "-" in titulo  # Contains date separators
        assert "202" in titulo  # Year prefix

    def test_gerar_titulo_contains_date(self) -> None:
        """Test that titulo contains a date in YYYY-MM-DD format."""
        # Arrange & Act
        titulo = GenerateReport._gerar_titulo()

        # Assert
        # Should match pattern "Análise Arquitetural - YYYY-MM-DD"
        parts = titulo.split(" - ")
        assert len(parts) == 2
        assert parts[0] == "Análise Arquitetural"
        date_part = parts[1]
        # Check date format YYYY-MM-DD
        assert len(date_part) == 10
        assert date_part[4] == "-"
        assert date_part[7] == "-"
