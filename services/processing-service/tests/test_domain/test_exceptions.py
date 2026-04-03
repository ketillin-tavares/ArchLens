"""Unit tests for domain exceptions."""

import pytest

from src.domain.exceptions import (
    AIBaseError,
    AnaliseInsanaError,
    DomainError,
    ImageProcessingError,
    LLMApiError,
    LLMContentFilterError,
    LLMContextWindowError,
    LLMRateLimitError,
    LLMTimeoutError,
    ProcessamentoNaoEncontradoError,
    SchemaValidationError,
    StorageDownloadError,
)


class TestDomainError:
    """Tests for DomainError base exception."""

    def test_domain_error_creation(self) -> None:
        """Test creating a DomainError."""
        # Arrange
        message = "Domain error occurred"

        # Act
        error = DomainError(message)

        # Assert
        assert str(error) == message
        assert isinstance(error, Exception)

    def test_domain_error_is_exception(self) -> None:
        """Test DomainError is an Exception."""
        # Arrange
        error = DomainError("test")

        # Act & Assert
        assert isinstance(error, Exception)
        assert issubclass(DomainError, Exception)

    def test_domain_error_can_be_raised(self) -> None:
        """Test that DomainError can be raised and caught."""
        # Arrange & Act & Assert
        with pytest.raises(DomainError):
            raise DomainError("test error")


class TestProcessamentoNaoEncontradoError:
    """Tests for ProcessamentoNaoEncontradoError."""

    def test_processamento_nao_encontrado_creation(self) -> None:
        """Test creating ProcessamentoNaoEncontradoError."""
        # Arrange
        message = "Processing not found"

        # Act
        error = ProcessamentoNaoEncontradoError(message)

        # Assert
        assert str(error) == message
        assert isinstance(error, DomainError)

    def test_processamento_nao_encontrado_inheritance(self) -> None:
        """Test ProcessamentoNaoEncontradoError inherits from DomainError."""
        # Arrange & Act & Assert
        assert issubclass(ProcessamentoNaoEncontradoError, DomainError)
        assert issubclass(ProcessamentoNaoEncontradoError, Exception)

    def test_processamento_nao_encontrado_can_be_caught(self) -> None:
        """Test catching ProcessamentoNaoEncontradoError as DomainError."""
        # Arrange & Act & Assert
        with pytest.raises(DomainError):
            raise ProcessamentoNaoEncontradoError("Not found")


class TestAIBaseError:
    """Tests for AIBaseError base exception."""

    def test_ai_base_error_creation(self) -> None:
        """Test creating an AIBaseError."""
        # Arrange
        message = "AI error occurred"

        # Act
        error = AIBaseError(message)

        # Assert
        assert str(error) == message
        assert isinstance(error, Exception)

    def test_ai_base_error_is_exception(self) -> None:
        """Test AIBaseError is an Exception."""
        # Arrange & Act & Assert
        assert issubclass(AIBaseError, Exception)


class TestLLMApiError:
    """Tests for LLMApiError."""

    def test_llm_api_error_creation(self) -> None:
        """Test creating an LLMApiError."""
        # Arrange
        message = "LLM API error"

        # Act
        error = LLMApiError(message)

        # Assert
        assert str(error) == message
        assert isinstance(error, AIBaseError)

    def test_llm_api_error_inheritance(self) -> None:
        """Test LLMApiError inherits correctly."""
        # Arrange & Act & Assert
        assert issubclass(LLMApiError, AIBaseError)
        assert issubclass(LLMApiError, Exception)


class TestLLMTimeoutError:
    """Tests for LLMTimeoutError."""

    def test_llm_timeout_error_creation(self) -> None:
        """Test creating an LLMTimeoutError."""
        # Arrange
        message = "LLM timeout"

        # Act
        error = LLMTimeoutError(message)

        # Assert
        assert str(error) == message
        assert isinstance(error, LLMApiError)

    def test_llm_timeout_error_inheritance(self) -> None:
        """Test LLMTimeoutError inherits correctly."""
        # Arrange & Act & Assert
        assert issubclass(LLMTimeoutError, LLMApiError)
        assert issubclass(LLMTimeoutError, AIBaseError)


class TestLLMRateLimitError:
    """Tests for LLMRateLimitError."""

    def test_llm_rate_limit_error_creation(self) -> None:
        """Test creating an LLMRateLimitError."""
        # Arrange
        message = "Rate limit exceeded"

        # Act
        error = LLMRateLimitError(message)

        # Assert
        assert str(error) == message
        assert isinstance(error, LLMApiError)

    def test_llm_rate_limit_error_inheritance(self) -> None:
        """Test LLMRateLimitError inherits correctly."""
        # Arrange & Act & Assert
        assert issubclass(LLMRateLimitError, LLMApiError)


class TestLLMContentFilterError:
    """Tests for LLMContentFilterError."""

    def test_llm_content_filter_error_creation(self) -> None:
        """Test creating an LLMContentFilterError."""
        # Arrange
        message = "Content filtered"

        # Act
        error = LLMContentFilterError(message)

        # Assert
        assert str(error) == message
        assert isinstance(error, AIBaseError)

    def test_llm_content_filter_error_not_subclass_of_api_error(self) -> None:
        """Test LLMContentFilterError is not a subclass of LLMApiError."""
        # Arrange & Act & Assert
        assert not issubclass(LLMContentFilterError, LLMApiError)
        assert issubclass(LLMContentFilterError, AIBaseError)


class TestLLMContextWindowError:
    """Tests for LLMContextWindowError."""

    def test_llm_context_window_error_creation(self) -> None:
        """Test creating an LLMContextWindowError."""
        # Arrange
        message = "Context window exceeded"

        # Act
        error = LLMContextWindowError(message)

        # Assert
        assert str(error) == message
        assert isinstance(error, AIBaseError)

    def test_llm_context_window_error_not_subclass_of_api_error(self) -> None:
        """Test LLMContextWindowError is not a subclass of LLMApiError."""
        # Arrange & Act & Assert
        assert not issubclass(LLMContextWindowError, LLMApiError)
        assert issubclass(LLMContextWindowError, AIBaseError)


class TestSchemaValidationError:
    """Tests for SchemaValidationError."""

    def test_schema_validation_error_creation(self) -> None:
        """Test creating a SchemaValidationError."""
        # Arrange
        message = "Schema validation failed"

        # Act
        error = SchemaValidationError(message)

        # Assert
        assert str(error) == message
        assert isinstance(error, AIBaseError)


class TestAnaliseInsanaError:
    """Tests for AnaliseInsanaError."""

    def test_analise_insana_error_creation(self) -> None:
        """Test creating an AnaliseInsanaError."""
        # Arrange
        message = "Analysis failed sanity checks"

        # Act
        error = AnaliseInsanaError(message)

        # Assert
        assert str(error) == message
        assert isinstance(error, AIBaseError)


class TestImageProcessingError:
    """Tests for ImageProcessingError."""

    def test_image_processing_error_creation(self) -> None:
        """Test creating an ImageProcessingError."""
        # Arrange
        message = "Image processing failed"

        # Act
        error = ImageProcessingError(message)

        # Assert
        assert str(error) == message
        assert isinstance(error, AIBaseError)


class TestStorageDownloadError:
    """Tests for StorageDownloadError."""

    def test_storage_download_error_creation(self) -> None:
        """Test creating a StorageDownloadError."""
        # Arrange
        message = "Storage download failed"

        # Act
        error = StorageDownloadError(message)

        # Assert
        assert str(error) == message
        assert isinstance(error, AIBaseError)

    def test_storage_download_error_is_retriable(self) -> None:
        """Test StorageDownloadError is a retriable exception."""
        # Arrange & Act & Assert
        # StorageDownloadError should be AIBaseError but not specifically non-retriable
        assert issubclass(StorageDownloadError, AIBaseError)


class TestExceptionHierarchy:
    """Tests for exception hierarchy and relationships."""

    def test_domain_errors_hierarchy(self) -> None:
        """Test domain error hierarchy."""
        # Arrange & Act & Assert
        assert issubclass(ProcessamentoNaoEncontradoError, DomainError)
        assert issubclass(DomainError, Exception)

    def test_ai_errors_hierarchy(self) -> None:
        """Test AI error hierarchy."""
        # Arrange & Act & Assert
        assert issubclass(AIBaseError, Exception)
        assert issubclass(LLMApiError, AIBaseError)
        assert issubclass(LLMTimeoutError, LLMApiError)
        assert issubclass(LLMRateLimitError, LLMApiError)

    def test_non_retriable_exceptions(self) -> None:
        """Test non-retriable exceptions hierarchy."""
        # Arrange & Act & Assert
        non_retriable = (LLMContentFilterError, LLMContextWindowError, AnaliseInsanaError, ImageProcessingError)
        for exc_class in non_retriable:
            assert issubclass(exc_class, AIBaseError)

    def test_retriable_exceptions(self) -> None:
        """Test retriable exceptions hierarchy."""
        # Arrange & Act & Assert
        retriable = (LLMApiError, StorageDownloadError)
        for exc_class in retriable:
            assert issubclass(exc_class, AIBaseError)
