"""Unit tests for validation module."""

from unittest.mock import AsyncMock

import pytest

from src.application.validation import validate_and_parse
from src.domain.exceptions import SchemaValidationError
from src.domain.schemas import AnaliseResultSchema


class TestValidateAndParse:
    """Tests for validate_and_parse function."""

    @pytest.mark.asyncio
    async def test_validate_and_parse_valid_json(self, sample_llm_response: str, mock_llm_client) -> None:
        """Test validating and parsing valid JSON."""
        # Arrange
        mock_llm_client = AsyncMock()

        # Act
        result = await validate_and_parse(sample_llm_response, mock_llm_client)

        # Assert
        assert isinstance(result, AnaliseResultSchema)
        assert len(result.componentes) == 2
        assert len(result.riscos) == 1

    @pytest.mark.asyncio
    async def test_validate_and_parse_invalid_json_then_corrected(self, mock_llm_client) -> None:
        """Test validation with invalid JSON that gets corrected by LLM."""
        # Arrange
        invalid_json = '{"componentes": [{"nome": "API", "tipo": "invalid_type"}], "riscos": []}'

        valid_response = """{
            "componentes": [
                {
                    "nome": "API Gateway",
                    "tipo": "api_gateway",
                    "confianca": 0.95,
                    "metadata": {"descricao": "API"}
                }
            ],
            "riscos": []
        }"""

        mock_llm_client.correct_json = AsyncMock(return_value=valid_response)

        # Act
        result = await validate_and_parse(invalid_json, mock_llm_client)

        # Assert
        assert isinstance(result, AnaliseResultSchema)
        mock_llm_client.correct_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_and_parse_json_decode_error(self, mock_llm_client) -> None:
        """Test validation with invalid JSON syntax."""
        # Arrange
        invalid_json = "not a json"

        valid_response = """{
            "componentes": [],
            "riscos": []
        }"""

        mock_llm_client.correct_json = AsyncMock(return_value=valid_response)

        # Act
        result = await validate_and_parse(invalid_json, mock_llm_client)

        # Assert
        assert isinstance(result, AnaliseResultSchema)
        mock_llm_client.correct_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_and_parse_correction_fails(self, mock_llm_client) -> None:
        """Test validation fails when correction also fails."""
        # Arrange
        invalid_json = "invalid"
        mock_llm_client.correct_json = AsyncMock(side_effect=Exception("LLM error"))

        # Act & Assert
        with pytest.raises(SchemaValidationError):
            await validate_and_parse(invalid_json, mock_llm_client)

    @pytest.mark.asyncio
    async def test_validate_and_parse_correction_returns_invalid(self, mock_llm_client) -> None:
        """Test validation fails when corrected JSON is still invalid."""
        # Arrange
        invalid_json = '{"componentes": "invalid"}'
        corrected_json = '{"componentes": "still invalid"}'

        mock_llm_client.correct_json = AsyncMock(return_value=corrected_json)

        # Act & Assert
        with pytest.raises(SchemaValidationError):
            await validate_and_parse(invalid_json, mock_llm_client)

    @pytest.mark.asyncio
    async def test_validate_and_parse_empty_result(self, mock_llm_client) -> None:
        """Test validating empty componentes and riscos."""
        # Arrange
        empty_json = '{"componentes": [], "riscos": []}'

        # Act
        result = await validate_and_parse(empty_json, mock_llm_client)

        # Assert
        assert isinstance(result, AnaliseResultSchema)
        assert result.componentes == []
        assert result.riscos == []
        mock_llm_client.correct_json.assert_not_called()

    @pytest.mark.asyncio
    async def test_validate_and_parse_missing_required_fields(self, mock_llm_client) -> None:
        """Test validation with missing required fields."""
        # Arrange
        incomplete_json = '{"componentes": []}'
        valid_response = '{"componentes": [], "riscos": []}'

        mock_llm_client.correct_json = AsyncMock(return_value=valid_response)

        # Act
        result = await validate_and_parse(incomplete_json, mock_llm_client)

        # Assert
        assert isinstance(result, AnaliseResultSchema)

    @pytest.mark.asyncio
    async def test_validate_and_parse_invalid_enum_values(self, mock_llm_client) -> None:
        """Test validation with invalid enum values gets corrected."""
        # Arrange
        invalid_tipos = """{
            "componentes": [
                {
                    "nome": "Service",
                    "tipo": "invalid_type",
                    "confianca": 0.9,
                    "metadata": {"descricao": "Test"}
                }
            ],
            "riscos": []
        }"""

        valid_response = """{
            "componentes": [
                {
                    "nome": "Service",
                    "tipo": "service",
                    "confianca": 0.9,
                    "metadata": {"descricao": "Test"}
                }
            ],
            "riscos": []
        }"""

        mock_llm_client.correct_json = AsyncMock(return_value=valid_response)

        # Act
        result = await validate_and_parse(invalid_tipos, mock_llm_client)

        # Assert
        assert isinstance(result, AnaliseResultSchema)
        assert result.componentes[0].tipo.value == "service"

    @pytest.mark.asyncio
    async def test_validate_and_parse_invalid_confianca_type(self, mock_llm_client) -> None:
        """Test validation with string confianca instead of float."""
        # Arrange
        invalid_confianca = """{
            "componentes": [
                {
                    "nome": "API",
                    "tipo": "api_gateway",
                    "confianca": "0.95",
                    "metadata": {"descricao": "Test"}
                }
            ],
            "riscos": []
        }"""

        valid_response = """{
            "componentes": [
                {
                    "nome": "API",
                    "tipo": "api_gateway",
                    "confianca": 0.95,
                    "metadata": {"descricao": "Test"}
                }
            ],
            "riscos": []
        }"""

        mock_llm_client.correct_json = AsyncMock(return_value=valid_response)

        # Act
        result = await validate_and_parse(invalid_confianca, mock_llm_client)

        # Assert
        assert isinstance(result, AnaliseResultSchema)
        assert isinstance(result.componentes[0].confianca, float)

    @pytest.mark.asyncio
    async def test_validate_and_parse_with_extra_fields(self, mock_llm_client) -> None:
        """Test validation ignores extra fields not in schema."""
        # Arrange
        extra_fields_json = """{
            "componentes": [
                {
                    "nome": "API",
                    "tipo": "api_gateway",
                    "confianca": 0.95,
                    "metadata": {"descricao": "Test"},
                    "extra_field": "should be ignored"
                }
            ],
            "riscos": [],
            "extra_root_field": "ignored"
        }"""

        # Act
        result = await validate_and_parse(extra_fields_json, mock_llm_client)

        # Assert
        assert isinstance(result, AnaliseResultSchema)
        mock_llm_client.correct_json.assert_not_called()
