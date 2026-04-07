"""Unit tests for infrastructure agents."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.infrastructure.agents.report_writer_agent import ReportWriterAgent
from src.infrastructure.agents.schemas import MarkdownReportOutput


class TestReportWriterAgent:
    """Tests for the ReportWriterAgent class."""

    @patch("src.infrastructure.agents.report_writer_agent.OpenAIProvider")
    @patch("src.infrastructure.agents.report_writer_agent.OpenAIChatModel")
    @patch("src.infrastructure.agents.report_writer_agent.Agent")
    def test_initialization(
        self,
        mock_agent_cls: MagicMock,
        mock_model_cls: MagicMock,
        mock_provider_cls: MagicMock,
    ) -> None:
        """Test that ReportWriterAgent initializes with correct model and prompt."""
        # Arrange
        mock_agent_instance = MagicMock()
        mock_agent_cls.__getitem__.return_value.return_value = mock_agent_instance

        # Act
        agent = ReportWriterAgent()

        # Assert
        mock_provider_cls.assert_called_once()
        mock_model_cls.assert_called_once()
        mock_agent_cls.__getitem__.assert_called_once()
        assert agent._agent == mock_agent_instance

    @patch("src.infrastructure.agents.report_writer_agent.OpenAIProvider")
    @patch("src.infrastructure.agents.report_writer_agent.OpenAIChatModel")
    @patch("src.infrastructure.agents.report_writer_agent.Agent")
    @pytest.mark.asyncio
    async def test_run_formats_prompt_and_returns_output(
        self,
        mock_agent_cls: MagicMock,
        mock_model_cls: MagicMock,
        mock_provider_cls: MagicMock,
    ) -> None:
        """Test that run formats the user prompt and returns MarkdownReportOutput."""
        # Arrange
        mock_output = MarkdownReportOutput(markdown="# Test Report\n" + "x" * 100)
        mock_result = MagicMock()
        mock_result.output = mock_output
        mock_agent_instance = MagicMock()
        mock_agent_instance.run = AsyncMock(return_value=mock_result)
        mock_agent_cls.__getitem__.return_value.return_value = mock_agent_instance

        # Act
        agent = ReportWriterAgent()
        result = await agent.run(
            titulo="Test Title",
            resumo="Test Summary",
            componentes=[{"id": "c1", "nome": "API"}],
            riscos=[{"id": "r1", "severidade": "alta"}],
            estatisticas={"total": 1},
        )

        # Assert
        assert isinstance(result, MarkdownReportOutput)
        assert result.markdown == mock_output.markdown
        mock_agent_instance.run.assert_called_once()
        # Verify the user prompt was passed (it's a string)
        call_args = mock_agent_instance.run.call_args
        assert "Test Title" in call_args[0][0]
        assert "Test Summary" in call_args[0][0]

    @patch("src.infrastructure.agents.report_writer_agent.OpenAIProvider")
    @patch("src.infrastructure.agents.report_writer_agent.OpenAIChatModel")
    @patch("src.infrastructure.agents.report_writer_agent.Agent")
    @pytest.mark.asyncio
    async def test_run_includes_all_data_in_prompt(
        self,
        mock_agent_cls: MagicMock,
        mock_model_cls: MagicMock,
        mock_provider_cls: MagicMock,
    ) -> None:
        """Test that run includes all data (componentes, riscos, estatisticas) in the prompt."""
        # Arrange
        mock_output = MarkdownReportOutput(markdown="# Test Report\n" + "x" * 100)
        mock_result = MagicMock()
        mock_result.output = mock_output
        mock_agent_instance = MagicMock()
        mock_agent_instance.run = AsyncMock(return_value=mock_result)
        mock_agent_cls.__getitem__.return_value.return_value = mock_agent_instance

        agent = ReportWriterAgent()

        componentes = [{"id": "c1", "nome": "API"}, {"id": "c2", "nome": "DB"}]
        riscos = [{"id": "r1", "severidade": "alta"}, {"id": "r2", "severidade": "média"}]
        estatisticas = {"total": 2, "criticas": 1}

        # Act
        await agent.run(
            titulo="Test Title",
            resumo="Test Summary",
            componentes=componentes,
            riscos=riscos,
            estatisticas=estatisticas,
        )

        # Assert
        call_args = mock_agent_instance.run.call_args
        prompt = call_args[0][0]
        # Verify all data is in the prompt as JSON strings
        assert "API" in prompt
        assert "DB" in prompt
        assert "alta" in prompt
        assert "média" in prompt
