"""Unit tests for domain schemas."""

import pytest
from pydantic import ValidationError

from src.domain.schemas import (
    AnaliseResultSchema,
    ComponenteMetadata,
    ComponenteSchema,
    RecomendacaoSchema,
    RiscoSchema,
    Severidade,
    TipoComponente,
)


class TestComponenteMetadata:
    """Tests for ComponenteMetadata schema."""

    def test_componente_metadata_creation(self) -> None:
        """Test creating ComponenteMetadata."""
        # Arrange
        descricao = "API Gateway serving client requests"

        # Act
        metadata = ComponenteMetadata(descricao=descricao)

        # Assert
        assert metadata.descricao == descricao

    def test_componente_metadata_min_length(self) -> None:
        """Test ComponenteMetadata requires non-empty description."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError):
            ComponenteMetadata(descricao="")

    def test_componente_metadata_max_length(self) -> None:
        """Test ComponenteMetadata has max length of 500."""
        # Arrange
        long_descricao = "x" * 501

        # Act & Assert
        with pytest.raises(ValidationError):
            ComponenteMetadata(descricao=long_descricao)

    def test_componente_metadata_at_boundaries(self) -> None:
        """Test ComponenteMetadata at min and max boundaries."""
        # Arrange
        min_descricao = "A"
        max_descricao = "x" * 500

        # Act
        metadata_min = ComponenteMetadata(descricao=min_descricao)
        metadata_max = ComponenteMetadata(descricao=max_descricao)

        # Assert
        assert len(metadata_min.descricao) == 1
        assert len(metadata_max.descricao) == 500


class TestComponenteSchema:
    """Tests for ComponenteSchema."""

    def test_componente_schema_creation_valid(self) -> None:
        """Test creating a valid ComponenteSchema."""
        # Arrange
        nome = "API Gateway"
        tipo = TipoComponente.API_GATEWAY
        confianca = 0.95
        metadata = ComponenteMetadata(descricao="Main API Gateway")

        # Act
        schema = ComponenteSchema(
            nome=nome,
            tipo=tipo,
            confianca=confianca,
            metadata=metadata,
        )

        # Assert
        assert schema.nome == nome
        assert schema.tipo == tipo
        assert schema.confianca == 0.95
        assert schema.metadata == metadata

    def test_componente_schema_all_tipos(self) -> None:
        """Test ComponenteSchema with all valid tipos."""
        # Arrange
        tipos_list = [
            TipoComponente.API_GATEWAY,
            TipoComponente.DATABASE,
            TipoComponente.QUEUE,
            TipoComponente.SERVICE,
            TipoComponente.LOAD_BALANCER,
            TipoComponente.CACHE,
            TipoComponente.STORAGE,
            TipoComponente.OTHER,
        ]
        metadata = ComponenteMetadata(descricao="Test")

        # Act & Assert
        for tipo in tipos_list:
            schema = ComponenteSchema(
                nome="Test",
                tipo=tipo,
                confianca=0.5,
                metadata=metadata,
            )
            assert schema.tipo == tipo

    def test_componente_schema_confianca_range(self) -> None:
        """Test confianca field is between 0.0 and 1.0."""
        # Arrange
        metadata = ComponenteMetadata(descricao="Test")

        # Act & Assert - Valid values
        for confianca in [0.0, 0.5, 0.99, 1.0]:
            schema = ComponenteSchema(
                nome="Test",
                tipo=TipoComponente.SERVICE,
                confianca=confianca,
                metadata=metadata,
            )
            assert schema.confianca == confianca

        # Act & Assert - Invalid values
        with pytest.raises(ValidationError):
            ComponenteSchema(
                nome="Test",
                tipo=TipoComponente.SERVICE,
                confianca=1.5,
                metadata=metadata,
            )

        with pytest.raises(ValidationError):
            ComponenteSchema(
                nome="Test",
                tipo=TipoComponente.SERVICE,
                confianca=-0.1,
                metadata=metadata,
            )

    def test_componente_schema_confianca_rounding(self) -> None:
        """Test confianca is rounded to 2 decimal places."""
        # Arrange
        metadata = ComponenteMetadata(descricao="Test")

        # Act
        schema = ComponenteSchema(
            nome="Test",
            tipo=TipoComponente.SERVICE,
            confianca=0.12345,
            metadata=metadata,
        )

        # Assert
        assert schema.confianca == 0.12

    def test_componente_schema_nome_min_length(self) -> None:
        """Test nome requires at least 1 character."""
        # Arrange
        metadata = ComponenteMetadata(descricao="Test")

        # Act & Assert
        with pytest.raises(ValidationError):
            ComponenteSchema(
                nome="",
                tipo=TipoComponente.SERVICE,
                confianca=0.5,
                metadata=metadata,
            )

    def test_componente_schema_nome_max_length(self) -> None:
        """Test nome max length is 255."""
        # Arrange
        metadata = ComponenteMetadata(descricao="Test")
        long_nome = "x" * 256

        # Act & Assert
        with pytest.raises(ValidationError):
            ComponenteSchema(
                nome=long_nome,
                tipo=TipoComponente.SERVICE,
                confianca=0.5,
                metadata=metadata,
            )


class TestRecomendacaoSchema:
    """Tests for RecomendacaoSchema."""

    def test_recomendacao_schema_creation(self) -> None:
        """Test creating a RecomendacaoSchema."""
        # Arrange
        descricao = "Implement load balancing"
        prioridade = Severidade.ALTA

        # Act
        schema = RecomendacaoSchema(
            descricao=descricao,
            prioridade=prioridade,
        )

        # Assert
        assert schema.descricao == descricao
        assert schema.prioridade == prioridade

    def test_recomendacao_schema_all_prioridades(self) -> None:
        """Test RecomendacaoSchema with all severidade values."""
        # Arrange
        prioridades = [Severidade.BAIXA, Severidade.MEDIA, Severidade.ALTA, Severidade.CRITICA]

        # Act & Assert
        for prioridade in prioridades:
            schema = RecomendacaoSchema(
                descricao="Test recommendation",
                prioridade=prioridade,
            )
            assert schema.prioridade == prioridade


class TestRiscoSchema:
    """Tests for RiscoSchema."""

    def test_risco_schema_creation_valid(self) -> None:
        """Test creating a valid RiscoSchema."""
        # Arrange
        descricao = "Single point of failure"
        severidade = Severidade.ALTA
        componentes_afetados = ["API Gateway", "Load Balancer"]
        recomendacao = RecomendacaoSchema(
            descricao="Implement redundancy",
            prioridade=Severidade.ALTA,
        )

        # Act
        schema = RiscoSchema(
            descricao=descricao,
            severidade=severidade,
            componentes_afetados=componentes_afetados,
            recomendacao=recomendacao,
        )

        # Assert
        assert schema.descricao == descricao
        assert schema.severidade == severidade
        assert schema.componentes_afetados == componentes_afetados
        assert schema.recomendacao == recomendacao

    def test_risco_schema_all_severidades(self) -> None:
        """Test RiscoSchema with all severidade values."""
        # Arrange
        severidades = [Severidade.BAIXA, Severidade.MEDIA, Severidade.ALTA, Severidade.CRITICA]
        recomendacao = RecomendacaoSchema(
            descricao="Test",
            prioridade=Severidade.MEDIA,
        )

        # Act & Assert
        for severidade in severidades:
            schema = RiscoSchema(
                descricao="Risk",
                severidade=severidade,
                componentes_afetados=["Component"],
                recomendacao=recomendacao,
            )
            assert schema.severidade == severidade

    def test_risco_schema_componentes_afetados_min_length(self) -> None:
        """Test componentes_afetados requires at least one component."""
        # Arrange
        recomendacao = RecomendacaoSchema(
            descricao="Test",
            prioridade=Severidade.MEDIA,
        )

        # Act & Assert
        with pytest.raises(ValidationError):
            RiscoSchema(
                descricao="Risk",
                severidade=Severidade.ALTA,
                componentes_afetados=[],
                recomendacao=recomendacao,
            )

    def test_risco_schema_multiple_affected_components(self) -> None:
        """Test RiscoSchema with multiple affected components."""
        # Arrange
        componentes = ["API Gateway", "Service A", "Database", "Cache"]
        recomendacao = RecomendacaoSchema(
            descricao="Test",
            prioridade=Severidade.ALTA,
        )

        # Act
        schema = RiscoSchema(
            descricao="Network latency",
            severidade=Severidade.MEDIA,
            componentes_afetados=componentes,
            recomendacao=recomendacao,
        )

        # Assert
        assert len(schema.componentes_afetados) == 4


class TestAnaliseResultSchema:
    """Tests for AnaliseResultSchema."""

    def test_analise_result_empty(self) -> None:
        """Test creating an empty AnaliseResultSchema."""
        # Act
        schema = AnaliseResultSchema()

        # Assert
        assert schema.componentes == []
        assert schema.riscos == []

    def test_analise_result_with_componentes_only(self) -> None:
        """Test AnaliseResultSchema with only componentes."""
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

        # Act
        schema = AnaliseResultSchema(componentes=componentes)

        # Assert
        assert len(schema.componentes) == 2
        assert schema.riscos == []

    def test_analise_result_with_complete_data(self) -> None:
        """Test AnaliseResultSchema with complete data."""
        # Arrange
        componentes = [
            ComponenteSchema(
                nome="API Gateway",
                tipo=TipoComponente.API_GATEWAY,
                confianca=0.95,
                metadata=ComponenteMetadata(descricao="API Gateway"),
            ),
            ComponenteSchema(
                nome="Database",
                tipo=TipoComponente.DATABASE,
                confianca=0.9,
                metadata=ComponenteMetadata(descricao="Database"),
            ),
        ]
        riscos = [
            RiscoSchema(
                descricao="Single point of failure",
                severidade=Severidade.ALTA,
                componentes_afetados=["API Gateway"],
                recomendacao=RecomendacaoSchema(
                    descricao="Implement redundancy",
                    prioridade=Severidade.ALTA,
                ),
            ),
        ]

        # Act
        schema = AnaliseResultSchema(componentes=componentes, riscos=riscos)

        # Assert
        assert len(schema.componentes) == 2
        assert len(schema.riscos) == 1

    def test_analise_result_risk_references_valid_components(self) -> None:
        """Test that risks must reference existing components."""
        # Arrange - Valid references
        componentes = [
            ComponenteSchema(
                nome="API Gateway",
                tipo=TipoComponente.API_GATEWAY,
                confianca=0.95,
                metadata=ComponenteMetadata(descricao="API"),
            ),
        ]
        riscos_valid = [
            RiscoSchema(
                descricao="Risk",
                severidade=Severidade.ALTA,
                componentes_afetados=["API Gateway"],
                recomendacao=RecomendacaoSchema(
                    descricao="Fix",
                    prioridade=Severidade.ALTA,
                ),
            ),
        ]

        # Act & Assert - Should succeed
        schema = AnaliseResultSchema(componentes=componentes, riscos=riscos_valid)
        assert len(schema.riscos) == 1

    def test_analise_result_risk_references_invalid_components(self) -> None:
        """Test that risks cannot reference non-existent components."""
        # Arrange
        componentes = [
            ComponenteSchema(
                nome="API Gateway",
                tipo=TipoComponente.API_GATEWAY,
                confianca=0.95,
                metadata=ComponenteMetadata(descricao="API"),
            ),
        ]
        riscos_invalid = [
            RiscoSchema(
                descricao="Risk",
                severidade=Severidade.ALTA,
                componentes_afetados=["NonExistentComponent"],
                recomendacao=RecomendacaoSchema(
                    descricao="Fix",
                    prioridade=Severidade.ALTA,
                ),
            ),
        ]

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            AnaliseResultSchema(componentes=componentes, riscos=riscos_invalid)

        assert "inexistentes" in str(exc_info.value).lower() or "invalid" in str(exc_info.value).lower()

    def test_analise_result_risk_references_multiple_components(self) -> None:
        """Test risk referencing multiple components."""
        # Arrange
        componentes = [
            ComponenteSchema(
                nome="API Gateway",
                tipo=TipoComponente.API_GATEWAY,
                confianca=0.95,
                metadata=ComponenteMetadata(descricao="API"),
            ),
            ComponenteSchema(
                nome="Database",
                tipo=TipoComponente.DATABASE,
                confianca=0.9,
                metadata=ComponenteMetadata(descricao="DB"),
            ),
            ComponenteSchema(
                nome="Cache",
                tipo=TipoComponente.CACHE,
                confianca=0.85,
                metadata=ComponenteMetadata(descricao="Cache"),
            ),
        ]
        riscos = [
            RiscoSchema(
                descricao="Network latency",
                severidade=Severidade.MEDIA,
                componentes_afetados=["API Gateway", "Database", "Cache"],
                recomendacao=RecomendacaoSchema(
                    descricao="Optimize network",
                    prioridade=Severidade.MEDIA,
                ),
            ),
        ]

        # Act
        schema = AnaliseResultSchema(componentes=componentes, riscos=riscos)

        # Assert
        assert len(schema.riscos[0].componentes_afetados) == 3
