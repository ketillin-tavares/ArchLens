"""Unit tests for LLM client."""

import inspect
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.domain.exceptions import (
    LLMApiError,
    LLMContentFilterError,
    LLMContextWindowError,
    LLMRateLimitError,
    LLMTimeoutError,
)
from src.infrastructure.llm.llm_client import PydanticAILLMClient


class TestPydanticAILLMClient:
    """Tests for PydanticAILLMClient."""

    def test_llm_client_interface_exists(self) -> None:
        """Test LLM client interface exists."""
        # Arrange & Act & Assert
        assert PydanticAILLMClient is not None

    def test_llm_client_has_required_methods(self) -> None:
        """Test LLM client has required methods defined."""
        # Arrange & Act
        methods = {m[0] for m in inspect.getmembers(PydanticAILLMClient, predicate=inspect.isfunction)}

        # Assert
        assert "analyze_image" in methods
        assert "correct_json" in methods

    @patch("src.infrastructure.llm.llm_client.OpenAIChatModel")
    @patch("src.infrastructure.llm.llm_client.get_settings")
    def test_llm_client_initialization(self, mock_get_settings, mock_model_class) -> None:
        """Test LLM client initialization with settings."""
        # Arrange
        mock_settings = MagicMock()
        mock_settings.llm.model_name = "gpt-4-vision"
        mock_settings.llm.base_url = "http://localhost:4000"
        mock_settings.llm.api_key = "test-key"
        mock_settings.llm.temperature = 0.7
        mock_settings.llm.max_tokens = 2000
        mock_get_settings.return_value = mock_settings
        mock_model_class.return_value = MagicMock()

        # Act
        client = PydanticAILLMClient()

        # Assert
        assert client is not None
        assert client._temperature == 0.7
        assert client._max_tokens == 2000

    @pytest.mark.asyncio
    @patch("src.infrastructure.llm.llm_client.Agent")
    @patch("src.infrastructure.llm.llm_client.OpenAIChatModel")
    @patch("src.infrastructure.llm.llm_client.get_settings")
    async def test_analyze_image_success(self, mock_get_settings, mock_model_class, mock_agent_class) -> None:
        """Test analyze_image successfully analyzes an image."""
        # Arrange
        mock_settings = MagicMock()
        mock_settings.llm.model_name = "gpt-4-vision"
        mock_settings.llm.base_url = "http://localhost:4000"
        mock_settings.llm.api_key = "test-key"
        mock_settings.llm.temperature = 0.7
        mock_settings.llm.max_tokens = 2000
        mock_get_settings.return_value = mock_settings
        mock_model_class.return_value = MagicMock()

        mock_agent = AsyncMock()
        mock_result = MagicMock()
        mock_result.model_dump_json.return_value = '{"componentes": [], "riscos": []}'
        mock_agent.run.return_value = mock_result
        mock_agent_class.return_value = mock_agent

        client = PydanticAILLMClient()

        # Act
        result = await client.analyze_image("base64data")

        # Assert
        assert result == '{"componentes": [], "riscos": []}'

    @pytest.mark.asyncio
    @patch("src.infrastructure.llm.llm_client.Agent")
    @patch("src.infrastructure.llm.llm_client.OpenAIChatModel")
    @patch("src.infrastructure.llm.llm_client.get_settings")
    async def test_analyze_image_timeout_error(self, mock_get_settings, mock_model_class, mock_agent_class) -> None:
        """Test analyze_image raises LLMTimeoutError on timeout."""
        # Arrange
        mock_settings = MagicMock()
        mock_settings.llm.model_name = "gpt-4-vision"
        mock_settings.llm.base_url = "http://localhost:4000"
        mock_settings.llm.api_key = "test-key"
        mock_settings.llm.temperature = 0.7
        mock_settings.llm.max_tokens = 2000
        mock_get_settings.return_value = mock_settings
        mock_model_class.return_value = MagicMock()

        mock_agent = AsyncMock()
        mock_agent.run.side_effect = Exception("Timeout: connection timed out")
        mock_agent_class.return_value = mock_agent

        client = PydanticAILLMClient()

        # Act & Assert
        with pytest.raises(LLMTimeoutError):
            await client.analyze_image("base64data")

    @pytest.mark.asyncio
    @patch("src.infrastructure.llm.llm_client.Agent")
    @patch("src.infrastructure.llm.llm_client.OpenAIChatModel")
    @patch("src.infrastructure.llm.llm_client.get_settings")
    async def test_analyze_image_rate_limit_error(self, mock_get_settings, mock_model_class, mock_agent_class) -> None:
        """Test analyze_image raises LLMRateLimitError on rate limit."""
        # Arrange
        mock_settings = MagicMock()
        mock_settings.llm.model_name = "gpt-4-vision"
        mock_settings.llm.base_url = "http://localhost:4000"
        mock_settings.llm.api_key = "test-key"
        mock_settings.llm.temperature = 0.7
        mock_settings.llm.max_tokens = 2000
        mock_get_settings.return_value = mock_settings
        mock_model_class.return_value = MagicMock()

        mock_agent = AsyncMock()
        mock_agent.run.side_effect = Exception("429 Too Many Requests")
        mock_agent_class.return_value = mock_agent

        client = PydanticAILLMClient()

        # Act & Assert
        with pytest.raises(LLMRateLimitError):
            await client.analyze_image("base64data")

    @pytest.mark.asyncio
    @patch("src.infrastructure.llm.llm_client.Agent")
    @patch("src.infrastructure.llm.llm_client.OpenAIChatModel")
    @patch("src.infrastructure.llm.llm_client.get_settings")
    async def test_analyze_image_content_filter_error(
        self, mock_get_settings, mock_model_class, mock_agent_class
    ) -> None:
        """Test analyze_image raises LLMContentFilterError on content filter."""
        # Arrange
        mock_settings = MagicMock()
        mock_settings.llm.model_name = "gpt-4-vision"
        mock_settings.llm.base_url = "http://localhost:4000"
        mock_settings.llm.api_key = "test-key"
        mock_settings.llm.temperature = 0.7
        mock_settings.llm.max_tokens = 2000
        mock_get_settings.return_value = mock_settings
        mock_model_class.return_value = MagicMock()

        mock_agent = AsyncMock()
        mock_agent.run.side_effect = Exception("Content_filter_triggered")
        mock_agent_class.return_value = mock_agent

        client = PydanticAILLMClient()

        # Act & Assert
        with pytest.raises(LLMContentFilterError):
            await client.analyze_image("base64data")

    @pytest.mark.asyncio
    @patch("src.infrastructure.llm.llm_client.Agent")
    @patch("src.infrastructure.llm.llm_client.OpenAIChatModel")
    @patch("src.infrastructure.llm.llm_client.get_settings")
    async def test_analyze_image_context_window_error(
        self, mock_get_settings, mock_model_class, mock_agent_class
    ) -> None:
        """Test analyze_image raises LLMContextWindowError on context window."""
        # Arrange
        mock_settings = MagicMock()
        mock_settings.llm.model_name = "gpt-4-vision"
        mock_settings.llm.base_url = "http://localhost:4000"
        mock_settings.llm.api_key = "test-key"
        mock_settings.llm.temperature = 0.7
        mock_settings.llm.max_tokens = 2000
        mock_get_settings.return_value = mock_settings
        mock_model_class.return_value = MagicMock()

        mock_agent = AsyncMock()
        mock_agent.run.side_effect = Exception("Context_length exceeded maximum")
        mock_agent_class.return_value = mock_agent

        client = PydanticAILLMClient()

        # Act & Assert
        with pytest.raises(LLMContextWindowError):
            await client.analyze_image("base64data")

    @pytest.mark.asyncio
    @patch("src.infrastructure.llm.llm_client.Agent")
    @patch("src.infrastructure.llm.llm_client.OpenAIChatModel")
    @patch("src.infrastructure.llm.llm_client.get_settings")
    async def test_correct_json_success(self, mock_get_settings, mock_model_class, mock_agent_class) -> None:
        """Test correct_json successfully corrects JSON."""
        # Arrange
        mock_settings = MagicMock()
        mock_settings.llm.model_name = "gpt-4-vision"
        mock_settings.llm.base_url = "http://localhost:4000"
        mock_settings.llm.api_key = "test-key"
        mock_settings.llm.temperature = 0.7
        mock_settings.llm.max_tokens = 2000
        mock_get_settings.return_value = mock_settings
        mock_model_class.return_value = MagicMock()

        mock_agent = AsyncMock()
        mock_result = MagicMock()
        mock_result.model_dump_json.return_value = '{"componentes": [], "riscos": []}'
        mock_agent.run.return_value = mock_result
        mock_agent_class.return_value = mock_agent

        client = PydanticAILLMClient()

        # Act
        result = await client.correct_json('{"invalid": "json"}', "Missing required fields")

        # Assert
        assert result == '{"componentes": [], "riscos": []}'

    @pytest.mark.asyncio
    @patch("src.infrastructure.llm.llm_client.Agent")
    @patch("src.infrastructure.llm.llm_client.OpenAIChatModel")
    @patch("src.infrastructure.llm.llm_client.get_settings")
    async def test_correct_json_error(self, mock_get_settings, mock_model_class, mock_agent_class) -> None:
        """Test correct_json raises error on failure."""
        # Arrange
        mock_settings = MagicMock()
        mock_settings.llm.model_name = "gpt-4-vision"
        mock_settings.llm.base_url = "http://localhost:4000"
        mock_settings.llm.api_key = "test-key"
        mock_settings.llm.temperature = 0.7
        mock_settings.llm.max_tokens = 2000
        mock_get_settings.return_value = mock_settings
        mock_model_class.return_value = MagicMock()

        mock_agent = AsyncMock()
        mock_agent.run.side_effect = Exception("General API error")
        mock_agent_class.return_value = mock_agent

        client = PydanticAILLMClient()

        # Act & Assert
        with pytest.raises(LLMApiError):
            await client.correct_json('{"invalid": "json"}', "Error")
