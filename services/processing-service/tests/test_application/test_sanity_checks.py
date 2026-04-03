"""Unit tests for sanity checks module."""

import pytest

from src.application.sanity_checks import check_sanity
from src.domain.exceptions import AnaliseInsanaError
from src.domain.schemas import AnaliseResultSchema, ComponenteMetadata, ComponenteSchema, TipoComponente


class TestCheckSanity:
    """Tests for the check_sanity function."""

    def test_check_sanity_empty_result(self) -> None:
        """Test sanity check passes for empty result."""
        # Arrange
        result = AnaliseResultSchema()

        # Act & Assert - Should not raise
        check_sanity(result)

    def test_check_sanity_normal_result(self) -> None:
        """Test sanity check passes for normal result."""
        # Arrange
        componentes = [
            ComponenteSchema(
                nome="API",
                tipo=TipoComponente.API_GATEWAY,
                confianca=0.9,
                metadata=ComponenteMetadata(descricao="API"),
            ),
            ComponenteSchema(
                nome="DB",
                tipo=TipoComponente.DATABASE,
                confianca=0.95,
                metadata=ComponenteMetadata(descricao="Database"),
            ),
        ]
        result = AnaliseResultSchema(componentes=componentes, riscos=[])

        # Act & Assert - Should not raise
        check_sanity(result)

    def test_check_sanity_too_many_componentes(self) -> None:
        """Test sanity check fails when too many componentes."""
        # Arrange - Create 31 components (exceeds MAX_COMPONENTES=30)
        componentes = [
            ComponenteSchema(
                nome=f"Component {i}",
                tipo=TipoComponente.SERVICE,
                confianca=0.9,
                metadata=ComponenteMetadata(descricao=f"Comp {i}"),
            )
            for i in range(31)
        ]
        result = AnaliseResultSchema(componentes=componentes)

        # Act & Assert
        with pytest.raises(AnaliseInsanaError) as exc_info:
            check_sanity(result)

        assert "excesso" in str(exc_info.value).lower() or "componentes" in str(exc_info.value).lower()

    def test_check_sanity_at_max_componentes_boundary(self) -> None:
        """Test sanity check passes at exact MAX_COMPONENTES boundary."""
        # Arrange - Create exactly 30 components (at MAX_COMPONENTES)
        componentes = [
            ComponenteSchema(
                nome=f"Component {i}",
                tipo=TipoComponente.SERVICE,
                confianca=0.9,
                metadata=ComponenteMetadata(descricao=f"Comp {i}"),
            )
            for i in range(30)
        ]
        result = AnaliseResultSchema(componentes=componentes)

        # Act & Assert - Should not raise
        check_sanity(result)

    def test_check_sanity_too_many_riscos(self) -> None:
        """Test sanity check fails when too many riscos."""
        # Arrange
        componentes = [
            ComponenteSchema(
                nome="Component",
                tipo=TipoComponente.SERVICE,
                confianca=0.9,
                metadata=ComponenteMetadata(descricao="Comp"),
            ),
        ]

        # Create 21 risks (exceeds MAX_RISCOS=20)
        from src.domain.schemas import RecomendacaoSchema, RiscoSchema, Severidade

        riscos = [
            RiscoSchema(
                descricao=f"Risk {i}",
                severidade=Severidade.MEDIA,
                componentes_afetados=["Component"],
                recomendacao=RecomendacaoSchema(
                    descricao=f"Fix {i}",
                    prioridade=Severidade.MEDIA,
                ),
            )
            for i in range(21)
        ]
        result = AnaliseResultSchema(componentes=componentes, riscos=riscos)

        # Act & Assert
        with pytest.raises(AnaliseInsanaError) as exc_info:
            check_sanity(result)

        assert "excesso" in str(exc_info.value).lower() or "riscos" in str(exc_info.value).lower()

    def test_check_sanity_at_max_riscos_boundary(self) -> None:
        """Test sanity check passes at exact MAX_RISCOS boundary."""
        # Arrange
        componentes = [
            ComponenteSchema(
                nome="Component",
                tipo=TipoComponente.SERVICE,
                confianca=0.9,
                metadata=ComponenteMetadata(descricao="Comp"),
            ),
        ]

        from src.domain.schemas import RecomendacaoSchema, RiscoSchema, Severidade

        riscos = [
            RiscoSchema(
                descricao=f"Risk {i}",
                severidade=Severidade.MEDIA,
                componentes_afetados=["Component"],
                recomendacao=RecomendacaoSchema(
                    descricao=f"Fix {i}",
                    prioridade=Severidade.MEDIA,
                ),
            )
            for i in range(20)
        ]
        result = AnaliseResultSchema(componentes=componentes, riscos=riscos)

        # Act & Assert - Should not raise
        check_sanity(result)

    def test_check_sanity_low_average_confidence(self) -> None:
        """Test sanity check fails when average confidence too low."""
        # Arrange - Create components with low confidence
        componentes = [
            ComponenteSchema(
                nome="Component",
                tipo=TipoComponente.SERVICE,
                confianca=0.3,  # Below MIN_CONFIANCA_MEDIA=0.4
                metadata=ComponenteMetadata(descricao="Comp"),
            ),
        ]
        result = AnaliseResultSchema(componentes=componentes)

        # Act & Assert
        with pytest.raises(AnaliseInsanaError) as exc_info:
            check_sanity(result)

        assert "confiança" in str(exc_info.value).lower() or "confidence" in str(exc_info.value).lower()

    def test_check_sanity_average_confidence_at_boundary(self) -> None:
        """Test sanity check passes at exact MIN_CONFIANCA_MEDIA boundary."""
        # Arrange - Create components with confidence at boundary
        componentes = [
            ComponenteSchema(
                nome="Component",
                tipo=TipoComponente.SERVICE,
                confianca=0.4,  # Exactly MIN_CONFIANCA_MEDIA=0.4
                metadata=ComponenteMetadata(descricao="Comp"),
            ),
        ]
        result = AnaliseResultSchema(componentes=componentes)

        # Act & Assert - Should not raise
        check_sanity(result)

    def test_check_sanity_average_confidence_mixed(self) -> None:
        """Test sanity check with mixed confidence values."""
        # Arrange - Average of [0.3, 0.5] = 0.4 (at boundary)
        componentes = [
            ComponenteSchema(
                nome="Component 1",
                tipo=TipoComponente.SERVICE,
                confianca=0.3,
                metadata=ComponenteMetadata(descricao="Comp1"),
            ),
            ComponenteSchema(
                nome="Component 2",
                tipo=TipoComponente.SERVICE,
                confianca=0.5,
                metadata=ComponenteMetadata(descricao="Comp2"),
            ),
        ]
        result = AnaliseResultSchema(componentes=componentes)

        # Act & Assert - Should not raise (average = 0.4)
        check_sanity(result)

    def test_check_sanity_average_confidence_below_boundary(self) -> None:
        """Test sanity check fails when average just below boundary."""
        # Arrange - Average of [0.35, 0.39] = 0.37 (below MIN_CONFIANCA_MEDIA=0.4)
        componentes = [
            ComponenteSchema(
                nome="Component 1",
                tipo=TipoComponente.SERVICE,
                confianca=0.35,
                metadata=ComponenteMetadata(descricao="Comp1"),
            ),
            ComponenteSchema(
                nome="Component 2",
                tipo=TipoComponente.SERVICE,
                confianca=0.39,
                metadata=ComponenteMetadata(descricao="Comp2"),
            ),
        ]
        result = AnaliseResultSchema(componentes=componentes)

        # Act & Assert
        with pytest.raises(AnaliseInsanaError) as exc_info:
            check_sanity(result)

        assert "confiança" in str(exc_info.value).lower() or "confidence" in str(exc_info.value).lower()

    def test_check_sanity_all_checks_pass(self) -> None:
        """Test sanity check passes when all checks pass."""
        # Arrange
        componentes = [
            ComponenteSchema(
                nome=f"Component {i}",
                tipo=TipoComponente.SERVICE,
                confianca=0.9,  # High confidence
                metadata=ComponenteMetadata(descricao=f"Comp {i}"),
            )
            for i in range(15)  # Below MAX_COMPONENTES=30
        ]

        from src.domain.schemas import RecomendacaoSchema, RiscoSchema, Severidade

        riscos = [
            RiscoSchema(
                descricao=f"Risk {i}",
                severidade=Severidade.MEDIA,
                componentes_afetados=[f"Component {i % 15}"],
                recomendacao=RecomendacaoSchema(
                    descricao=f"Fix {i}",
                    prioridade=Severidade.MEDIA,
                ),
            )
            for i in range(10)  # Below MAX_RISCOS=20
        ]
        result = AnaliseResultSchema(componentes=componentes, riscos=riscos)

        # Act & Assert - Should not raise
        check_sanity(result)

    def test_check_sanity_high_confidence_components(self) -> None:
        """Test sanity check with high confidence components."""
        # Arrange
        componentes = [
            ComponenteSchema(
                nome="Component",
                tipo=TipoComponente.SERVICE,
                confianca=1.0,  # Maximum confidence
                metadata=ComponenteMetadata(descricao="Comp"),
            ),
        ]
        result = AnaliseResultSchema(componentes=componentes)

        # Act & Assert
        check_sanity(result)
