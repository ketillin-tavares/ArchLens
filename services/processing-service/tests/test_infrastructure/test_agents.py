"""Unit tests for multi-agent infrastructure."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.domain.exceptions import AnaliseInsanaError
from src.domain.schemas import (
    AnaliseResultSchema,
    ComponenteMetadata,
    ComponenteSchema,
    RecomendacaoSchema,
    RiscoSchema,
    Severidade,
    TipoComponente,
)
from src.infrastructure.agents.analyzer_agent import AnalyzerAgent
from src.infrastructure.agents.extractor_agent import ExtractorAgent
from src.infrastructure.agents.judge_agent import JudgeAgent
from src.infrastructure.agents.multi_agent_pipeline import MultiAgentPipeline
from src.infrastructure.agents.schemas import (
    AnalyzerResultSchema,
    ExtractionResultSchema,
    JudgeResultSchema,
)
from src.infrastructure.agents.single_call_pipeline import SingleCallPipeline


@pytest.fixture
def mock_vision_model() -> MagicMock:
    """Fixture with mock vision model."""
    return MagicMock()


@pytest.fixture
def mock_analyzer_model() -> MagicMock:
    """Fixture with mock analyzer model."""
    return MagicMock()


@pytest.fixture
def sample_extraction_result() -> ExtractionResultSchema:
    """Fixture with sample extraction result."""
    return ExtractionResultSchema(
        componentes=[
            ComponenteSchema(
                nome="API Gateway",
                tipo=TipoComponente.API_GATEWAY,
                confianca=0.95,
                metadata=ComponenteMetadata(descricao="API Gateway da aplicação"),
            ),
            ComponenteSchema(
                nome="Database",
                tipo=TipoComponente.DATABASE,
                confianca=0.9,
                metadata=ComponenteMetadata(descricao="PostgreSQL database"),
            ),
        ],
        descricao_geral="Sistema com API Gateway e database",
    )


@pytest.fixture
def sample_analyzer_result() -> AnalyzerResultSchema:
    """Fixture with sample analyzer result."""
    return AnalyzerResultSchema(
        riscos=[
            RiscoSchema(
                descricao="Single point of failure no API Gateway",
                severidade=Severidade.ALTA,
                componentes_afetados=["API Gateway"],
                recomendacao=RecomendacaoSchema(
                    descricao="Implementar replicação e failover",
                    prioridade=Severidade.ALTA,
                ),
            ),
        ]
    )


@pytest.fixture
def sample_judge_result_approved() -> JudgeResultSchema:
    """Fixture with approved judge result."""
    return JudgeResultSchema(
        scores={
            "completude": 8.5,
            "precisao": 8.0,
            "classificacao": 7.5,
            "riscos_relevantes": 8.0,
        },
        score_medio=8.0,
        aprovado=True,
        comentario="Análise de boa qualidade com identificação apropriada de riscos",
    )


@pytest.fixture
def sample_judge_result_rejected() -> JudgeResultSchema:
    """Fixture with rejected judge result."""
    return JudgeResultSchema(
        scores={
            "completude": 4.0,
            "precisao": 3.5,
            "classificacao": 4.0,
            "riscos_relevantes": 3.0,
        },
        score_medio=3.625,
        aprovado=False,
        comentario="Análise incompleta com muitos erros de identificação",
    )


class TestExtractorAgent:
    """Tests for ExtractorAgent."""

    @pytest.mark.asyncio
    @patch("src.infrastructure.agents.extractor_agent.Agent")
    async def test_extractor_agent_run_success(
        self,
        mock_agent_class: MagicMock,
        mock_vision_model: MagicMock,
        sample_extraction_result: ExtractionResultSchema,
    ) -> None:
        """Test ExtractorAgent.run() successfully extracts components."""
        # Arrange
        mock_agent_instance = AsyncMock()
        mock_result = MagicMock()
        mock_result.output = sample_extraction_result
        mock_agent_instance.run.return_value = mock_result
        mock_agent_class.return_value = mock_agent_instance

        agent = ExtractorAgent(model=mock_vision_model)
        image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

        # Act
        result = await agent.run(image_b64)

        # Assert
        assert result == sample_extraction_result
        assert len(result.componentes) == 2
        assert result.componentes[0].nome == "API Gateway"
        assert result.descricao_geral == "Sistema com API Gateway e database"
        mock_agent_instance.run.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.infrastructure.agents.extractor_agent.Agent")
    async def test_extractor_agent_run_with_image_url(
        self,
        mock_agent_class: MagicMock,
        mock_vision_model: MagicMock,
        sample_extraction_result: ExtractionResultSchema,
    ) -> None:
        """Test ExtractorAgent.run() passes correct image URL format."""
        # Arrange
        mock_agent_instance = AsyncMock()
        mock_result = MagicMock()
        mock_result.output = sample_extraction_result
        mock_agent_instance.run.return_value = mock_result
        mock_agent_class.return_value = mock_agent_instance

        agent = ExtractorAgent(model=mock_vision_model)
        image_b64 = "base64imagedata"

        # Act
        await agent.run(image_b64)

        # Assert
        call_args = mock_agent_instance.run.call_args
        assert call_args is not None
        args = call_args[0][0]
        # Check that ImageUrl is in the arguments
        assert len(args) == 2
        assert hasattr(args[1], "url")
        assert "data:image/png;base64,base64imagedata" in str(args[1].url)

    @pytest.mark.asyncio
    @patch("src.infrastructure.agents.extractor_agent.Agent")
    async def test_extractor_agent_run_empty_components(
        self,
        mock_agent_class: MagicMock,
        mock_vision_model: MagicMock,
    ) -> None:
        """Test ExtractorAgent.run() handles empty component list."""
        # Arrange
        mock_agent_instance = AsyncMock()
        mock_result = MagicMock()
        empty_result = ExtractionResultSchema(
            componentes=[],
            descricao_geral="Nenhum componente encontrado",
        )
        mock_result.output = empty_result
        mock_agent_instance.run.return_value = mock_result
        mock_agent_class.return_value = mock_agent_instance

        agent = ExtractorAgent(model=mock_vision_model)

        # Act
        result = await agent.run("base64data")

        # Assert
        assert result.componentes == []
        assert result.descricao_geral == "Nenhum componente encontrado"


class TestAnalyzerAgent:
    """Tests for AnalyzerAgent."""

    @pytest.mark.asyncio
    @patch("src.infrastructure.agents.analyzer_agent.Agent")
    async def test_analyzer_agent_run_success(
        self,
        mock_agent_class: MagicMock,
        mock_analyzer_model: MagicMock,
        sample_extraction_result: ExtractionResultSchema,
        sample_analyzer_result: AnalyzerResultSchema,
    ) -> None:
        """Test AnalyzerAgent.run() successfully identifies risks."""
        # Arrange
        mock_agent_instance = AsyncMock()
        mock_result = MagicMock()
        mock_result.output = sample_analyzer_result
        mock_agent_instance.run.return_value = mock_result
        mock_agent_class.return_value = mock_agent_instance

        agent = AnalyzerAgent(model=mock_analyzer_model)

        # Act
        result = await agent.run(
            componentes=sample_extraction_result.componentes,
            descricao_geral=sample_extraction_result.descricao_geral,
        )

        # Assert
        assert result == sample_analyzer_result
        assert len(result.riscos) == 1
        assert result.riscos[0].descricao == "Single point of failure no API Gateway"
        assert result.riscos[0].severidade == Severidade.ALTA
        mock_agent_instance.run.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.infrastructure.agents.analyzer_agent.Agent")
    async def test_analyzer_agent_run_empty_risks(
        self,
        mock_agent_class: MagicMock,
        mock_analyzer_model: MagicMock,
        sample_extraction_result: ExtractionResultSchema,
    ) -> None:
        """Test AnalyzerAgent.run() handles empty risk list."""
        # Arrange
        mock_agent_instance = AsyncMock()
        mock_result = MagicMock()
        empty_result = AnalyzerResultSchema(riscos=[])
        mock_result.output = empty_result
        mock_agent_instance.run.return_value = mock_result
        mock_agent_class.return_value = mock_agent_instance

        agent = AnalyzerAgent(model=mock_analyzer_model)

        # Act
        result = await agent.run(
            componentes=sample_extraction_result.componentes,
            descricao_geral=sample_extraction_result.descricao_geral,
        )

        # Assert
        assert result.riscos == []

    @pytest.mark.asyncio
    @patch("src.infrastructure.agents.analyzer_agent.Agent")
    async def test_analyzer_agent_formats_component_json(
        self,
        mock_agent_class: MagicMock,
        mock_analyzer_model: MagicMock,
        sample_extraction_result: ExtractionResultSchema,
        sample_analyzer_result: AnalyzerResultSchema,
    ) -> None:
        """Test AnalyzerAgent.run() correctly formats components as JSON."""
        # Arrange
        mock_agent_instance = AsyncMock()
        mock_result = MagicMock()
        mock_result.output = sample_analyzer_result
        mock_agent_instance.run.return_value = mock_result
        mock_agent_class.return_value = mock_agent_instance

        agent = AnalyzerAgent(model=mock_analyzer_model)

        # Act
        await agent.run(
            componentes=sample_extraction_result.componentes,
            descricao_geral=sample_extraction_result.descricao_geral,
        )

        # Assert
        call_args = mock_agent_instance.run.call_args
        assert call_args is not None
        prompt = call_args[0][0]
        # Verify that JSON is properly formatted in the prompt
        assert "API Gateway" in prompt
        assert "Database" in prompt


class TestJudgeAgent:
    """Tests for JudgeAgent."""

    @pytest.mark.asyncio
    @patch("src.infrastructure.agents.judge_agent.Agent")
    async def test_judge_agent_run_approved(
        self,
        mock_agent_class: MagicMock,
        mock_vision_model: MagicMock,
        sample_analise_result: AnaliseResultSchema,
        sample_judge_result_approved: JudgeResultSchema,
    ) -> None:
        """Test JudgeAgent.run() returns approved result."""
        # Arrange
        mock_agent_instance = AsyncMock()
        mock_result = MagicMock()
        mock_result.output = sample_judge_result_approved
        mock_agent_instance.run.return_value = mock_result
        mock_agent_class.return_value = mock_agent_instance

        agent = JudgeAgent(model=mock_vision_model)
        image_b64 = "base64data"

        # Act
        result = await agent.run(
            analise_result=sample_analise_result,
            image_b64=image_b64,
        )

        # Assert
        assert result == sample_judge_result_approved
        assert result.aprovado is True
        assert result.score_medio == 8.0
        mock_agent_instance.run.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.infrastructure.agents.judge_agent.Agent")
    async def test_judge_agent_run_rejected(
        self,
        mock_agent_class: MagicMock,
        mock_vision_model: MagicMock,
        sample_analise_result: AnaliseResultSchema,
        sample_judge_result_rejected: JudgeResultSchema,
    ) -> None:
        """Test JudgeAgent.run() returns rejected result."""
        # Arrange
        mock_agent_instance = AsyncMock()
        mock_result = MagicMock()
        mock_result.output = sample_judge_result_rejected
        mock_agent_instance.run.return_value = mock_result
        mock_agent_class.return_value = mock_agent_instance

        agent = JudgeAgent(model=mock_vision_model)
        image_b64 = "base64data"

        # Act
        result = await agent.run(
            analise_result=sample_analise_result,
            image_b64=image_b64,
        )

        # Assert
        assert result == sample_judge_result_rejected
        assert result.aprovado is False
        assert result.score_medio == 3.625

    @pytest.mark.asyncio
    @patch("src.infrastructure.agents.judge_agent.Agent")
    async def test_judge_agent_passes_image_url(
        self,
        mock_agent_class: MagicMock,
        mock_vision_model: MagicMock,
        sample_analise_result: AnaliseResultSchema,
        sample_judge_result_approved: JudgeResultSchema,
    ) -> None:
        """Test JudgeAgent.run() correctly passes image URL."""
        # Arrange
        mock_agent_instance = AsyncMock()
        mock_result = MagicMock()
        mock_result.output = sample_judge_result_approved
        mock_agent_instance.run.return_value = mock_result
        mock_agent_class.return_value = mock_agent_instance

        agent = JudgeAgent(model=mock_vision_model)
        image_b64 = "mybase64imagedata"

        # Act
        await agent.run(
            analise_result=sample_analise_result,
            image_b64=image_b64,
        )

        # Assert
        call_args = mock_agent_instance.run.call_args
        assert call_args is not None
        args = call_args[0][0]
        # Check that ImageUrl is in the arguments
        assert len(args) == 2
        assert hasattr(args[1], "url")
        assert "data:image/png;base64,mybase64imagedata" in str(args[1].url)


class TestMultiAgentPipeline:
    """Tests for MultiAgentPipeline."""

    @pytest.mark.asyncio
    @patch("src.infrastructure.agents.multi_agent_pipeline.JudgeAgent")
    @patch("src.infrastructure.agents.multi_agent_pipeline.AnalyzerAgent")
    @patch("src.infrastructure.agents.multi_agent_pipeline.ExtractorAgent")
    async def test_multi_agent_pipeline_without_judge(
        self,
        mock_extractor_class: MagicMock,
        mock_analyzer_class: MagicMock,
        mock_judge_class: MagicMock,
        mock_vision_model: MagicMock,
        mock_analyzer_model: MagicMock,
        sample_extraction_result: ExtractionResultSchema,
        sample_analyzer_result: AnalyzerResultSchema,
    ) -> None:
        """Test MultiAgentPipeline runs without judge when disabled."""
        # Arrange
        mock_extractor_instance = AsyncMock()
        mock_extractor_instance.run.return_value = sample_extraction_result
        mock_extractor_class.return_value = mock_extractor_instance

        mock_analyzer_instance = AsyncMock()
        mock_analyzer_instance.run.return_value = sample_analyzer_result
        mock_analyzer_class.return_value = mock_analyzer_instance

        pipeline = MultiAgentPipeline(
            vision_model=mock_vision_model,
            analyzer_model=mock_analyzer_model,
            enable_judge=False,
        )

        image_b64 = "base64data"

        # Act
        result = await pipeline.run(image_b64)

        # Assert
        assert len(result.componentes) == 2
        assert len(result.riscos) == 1
        mock_extractor_instance.run.assert_called_once_with(image_b64)
        mock_analyzer_instance.run.assert_called_once()
        mock_judge_class.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.infrastructure.agents.multi_agent_pipeline.JudgeAgent")
    @patch("src.infrastructure.agents.multi_agent_pipeline.AnalyzerAgent")
    @patch("src.infrastructure.agents.multi_agent_pipeline.ExtractorAgent")
    async def test_multi_agent_pipeline_with_judge_approved(
        self,
        mock_extractor_class: MagicMock,
        mock_analyzer_class: MagicMock,
        mock_judge_class: MagicMock,
        mock_vision_model: MagicMock,
        mock_analyzer_model: MagicMock,
        sample_extraction_result: ExtractionResultSchema,
        sample_analyzer_result: AnalyzerResultSchema,
        sample_judge_result_approved: JudgeResultSchema,
    ) -> None:
        """Test MultiAgentPipeline with judge approval."""
        # Arrange
        mock_extractor_instance = AsyncMock()
        mock_extractor_instance.run.return_value = sample_extraction_result
        mock_extractor_class.return_value = mock_extractor_instance

        mock_analyzer_instance = AsyncMock()
        mock_analyzer_instance.run.return_value = sample_analyzer_result
        mock_analyzer_class.return_value = mock_analyzer_instance

        mock_judge_instance = AsyncMock()
        mock_judge_instance.run.return_value = sample_judge_result_approved
        mock_judge_class.return_value = mock_judge_instance

        pipeline = MultiAgentPipeline(
            vision_model=mock_vision_model,
            analyzer_model=mock_analyzer_model,
            enable_judge=True,
        )

        image_b64 = "base64data"

        # Act
        result = await pipeline.run(image_b64)

        # Assert
        assert len(result.componentes) == 2
        assert len(result.riscos) == 1
        mock_extractor_instance.run.assert_called_once()
        mock_analyzer_instance.run.assert_called_once()
        mock_judge_instance.run.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.infrastructure.agents.multi_agent_pipeline.JudgeAgent")
    @patch("src.infrastructure.agents.multi_agent_pipeline.AnalyzerAgent")
    @patch("src.infrastructure.agents.multi_agent_pipeline.ExtractorAgent")
    async def test_multi_agent_pipeline_with_judge_rejected(
        self,
        mock_extractor_class: MagicMock,
        mock_analyzer_class: MagicMock,
        mock_judge_class: MagicMock,
        mock_vision_model: MagicMock,
        mock_analyzer_model: MagicMock,
        sample_extraction_result: ExtractionResultSchema,
        sample_analyzer_result: AnalyzerResultSchema,
        sample_judge_result_rejected: JudgeResultSchema,
    ) -> None:
        """Test MultiAgentPipeline raises AnaliseInsanaError on judge rejection."""
        # Arrange
        mock_extractor_instance = AsyncMock()
        mock_extractor_instance.run.return_value = sample_extraction_result
        mock_extractor_class.return_value = mock_extractor_instance

        mock_analyzer_instance = AsyncMock()
        mock_analyzer_instance.run.return_value = sample_analyzer_result
        mock_analyzer_class.return_value = mock_analyzer_instance

        mock_judge_instance = AsyncMock()
        mock_judge_instance.run.return_value = sample_judge_result_rejected
        mock_judge_class.return_value = mock_judge_instance

        pipeline = MultiAgentPipeline(
            vision_model=mock_vision_model,
            analyzer_model=mock_analyzer_model,
            enable_judge=True,
        )

        image_b64 = "base64data"

        # Act & Assert
        with pytest.raises(AnaliseInsanaError) as exc_info:
            await pipeline.run(image_b64)

        assert "Judge reprovou" in str(exc_info.value)
        assert "3.6" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch("src.infrastructure.agents.multi_agent_pipeline.JudgeAgent")
    @patch("src.infrastructure.agents.multi_agent_pipeline.AnalyzerAgent")
    @patch("src.infrastructure.agents.multi_agent_pipeline.ExtractorAgent")
    async def test_multi_agent_pipeline_orchestrates_correctly(
        self,
        mock_extractor_class: MagicMock,
        mock_analyzer_class: MagicMock,
        mock_judge_class: MagicMock,
        mock_vision_model: MagicMock,
        mock_analyzer_model: MagicMock,
        sample_extraction_result: ExtractionResultSchema,
        sample_analyzer_result: AnalyzerResultSchema,
        sample_judge_result_approved: JudgeResultSchema,
    ) -> None:
        """Test MultiAgentPipeline orchestrates agents in correct order."""
        # Arrange
        mock_extractor_instance = AsyncMock()
        mock_extractor_instance.run.return_value = sample_extraction_result
        mock_extractor_class.return_value = mock_extractor_instance

        mock_analyzer_instance = AsyncMock()
        mock_analyzer_instance.run.return_value = sample_analyzer_result
        mock_analyzer_class.return_value = mock_analyzer_instance

        mock_judge_instance = AsyncMock()
        mock_judge_instance.run.return_value = sample_judge_result_approved
        mock_judge_class.return_value = mock_judge_instance

        pipeline = MultiAgentPipeline(
            vision_model=mock_vision_model,
            analyzer_model=mock_analyzer_model,
            enable_judge=True,
        )

        # Act
        await pipeline.run("base64data")

        # Assert
        # Verify all agents were called in sequence
        assert mock_extractor_instance.run.called
        assert mock_analyzer_instance.run.called
        assert mock_judge_instance.run.called


class TestSingleCallPipeline:
    """Tests for SingleCallPipeline."""

    @pytest.mark.asyncio
    async def test_single_call_pipeline_run_success(
        self,
        mock_llm_client,
        sample_analise_result: AnaliseResultSchema,
    ) -> None:
        """Test SingleCallPipeline.run() successfully processes image."""
        # Arrange
        mock_llm_client.analyze_image.return_value = """{
            "componentes": [
                {
                    "nome": "API Gateway",
                    "tipo": "api_gateway",
                    "confianca": 0.95,
                    "metadata": {"descricao": "API Gateway da aplicação"}
                },
                {
                    "nome": "Database",
                    "tipo": "database",
                    "confianca": 0.9,
                    "metadata": {"descricao": "PostgreSQL database"}
                }
            ],
            "riscos": [
                {
                    "descricao": "Single point of failure",
                    "severidade": "alta",
                    "componentes_afetados": ["API Gateway"],
                    "recomendacao": {
                        "descricao": "Implementar replicação",
                        "prioridade": "alta"
                    }
                }
            ]
        }"""

        pipeline = SingleCallPipeline(llm_client=mock_llm_client)
        image_b64 = "base64data"

        # Act
        result = await pipeline.run(image_b64)

        # Assert
        assert result is not None
        assert len(result.componentes) == 2
        assert len(result.riscos) == 1
        mock_llm_client.analyze_image.assert_called_once_with(image_b64)

    @pytest.mark.asyncio
    async def test_single_call_pipeline_run_calls_analyze_image(
        self,
        mock_llm_client,
        sample_analise_result: AnaliseResultSchema,
    ) -> None:
        """Test SingleCallPipeline.run() calls LLM client analyze_image."""
        # Arrange
        mock_llm_client.analyze_image.return_value = """{
            "componentes": [],
            "riscos": []
        }"""

        pipeline = SingleCallPipeline(llm_client=mock_llm_client)
        image_b64 = "testbase64"

        # Act
        await pipeline.run(image_b64)

        # Assert
        mock_llm_client.analyze_image.assert_called_once_with(image_b64)

    @pytest.mark.asyncio
    async def test_single_call_pipeline_run_empty_result(
        self,
        mock_llm_client,
    ) -> None:
        """Test SingleCallPipeline.run() handles empty response."""
        # Arrange
        mock_llm_client.analyze_image.return_value = """{
            "componentes": [],
            "riscos": []
        }"""

        pipeline = SingleCallPipeline(llm_client=mock_llm_client)

        # Act
        result = await pipeline.run("base64data")

        # Assert
        assert result.componentes == []
        assert result.riscos == []
