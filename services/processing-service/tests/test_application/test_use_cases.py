"""Unit tests for application use cases."""

import uuid

import pytest

from src.application.use_cases.get_processing_result import GetProcessingResult
from src.application.use_cases.process_diagram import ProcessDiagram
from src.domain.entities import Componente, Processamento, Risco, StatusProcessamento
from src.domain.exceptions import (
    ImageProcessingError,
    LLMContentFilterError,
    LLMTimeoutError,
    ProcessamentoNaoEncontradoError,
    SchemaValidationError,
    StorageDownloadError,
)
from src.domain.schemas import (
    AnaliseResultSchema,
    ComponenteMetadata,
    ComponenteSchema,
    TipoComponente,
)


class TestProcessDiagram:
    """Tests for the ProcessDiagram use case."""

    @pytest.mark.asyncio
    async def test_process_diagram_happy_path(
        self,
        analise_id: uuid.UUID,
        processamento_id: uuid.UUID,
        mock_processamento_repository,
        mock_event_publisher,
        mock_file_storage,
        mock_image_processor,
        mock_analysis_pipeline,
        sample_processamento,
        sample_analise_result,
        sample_image_bytes,
    ) -> None:
        """Test ProcessDiagram happy path: successfully analyze a diagram."""
        # Arrange
        processamento = Processamento(analise_id=analise_id)
        mock_processamento_repository.buscar_por_analise_id.return_value = None
        mock_processamento_repository.salvar_processamento.return_value = processamento
        mock_processamento_repository.salvar_componentes.return_value = [
            Componente(
                processamento_id=processamento.id,
                nome="API Gateway",
                tipo="api_gateway",
                confianca=0.95,
            ),
        ]
        mock_processamento_repository.salvar_riscos.return_value = [
            Risco(
                processamento_id=processamento.id,
                descricao="Risk",
                severidade="alta",
                componentes_afetados=["API Gateway"],
            ),
        ]

        mock_file_storage.download_file.return_value = sample_image_bytes
        mock_image_processor.normalize.return_value = "iVBORw0KGgo="
        mock_analysis_pipeline.run.return_value = sample_analise_result

        use_case = ProcessDiagram(
            processamento_repository=mock_processamento_repository,
            event_publisher=mock_event_publisher,
            file_storage=mock_file_storage,
            image_processor=mock_image_processor,
            analysis_pipeline=mock_analysis_pipeline,
        )

        # Act
        await use_case.execute(str(analise_id), "diagrama.pdf", "application/pdf")

        # Assert
        mock_file_storage.download_file.assert_called_once_with("diagrama.pdf")
        mock_image_processor.normalize.assert_called_once()
        mock_analysis_pipeline.run.assert_called_once()
        assert mock_event_publisher.publish_event.call_count >= 2  # ProcessamentoIniciado + AnaliseConcluida

    @pytest.mark.asyncio
    async def test_process_diagram_idempotency_already_completed(
        self,
        analise_id: uuid.UUID,
        mock_processamento_repository,
        mock_event_publisher,
        mock_file_storage,
        mock_image_processor,
        mock_analysis_pipeline,
    ) -> None:
        """Test ProcessDiagram skips processing if already completed."""
        # Arrange
        completed_processamento = Processamento(
            analise_id=analise_id,
            status=StatusProcessamento.CONCLUIDO,
        )
        mock_processamento_repository.buscar_por_analise_id.return_value = completed_processamento

        use_case = ProcessDiagram(
            processamento_repository=mock_processamento_repository,
            event_publisher=mock_event_publisher,
            file_storage=mock_file_storage,
            image_processor=mock_image_processor,
            analysis_pipeline=mock_analysis_pipeline,
        )

        # Act
        await use_case.execute(str(analise_id), "diagrama.pdf", "application/pdf")

        # Assert
        # Should not process further
        mock_file_storage.download_file.assert_not_called()
        mock_event_publisher.publish_event.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_diagram_retry_on_error(
        self,
        analise_id: uuid.UUID,
        mock_processamento_repository,
        mock_event_publisher,
        mock_file_storage,
        mock_image_processor,
        mock_analysis_pipeline,
        sample_image_bytes,
    ) -> None:
        """Test ProcessDiagram retries on error status."""
        # Arrange
        failed_processamento = Processamento(
            analise_id=analise_id,
            status=StatusProcessamento.ERRO,
            tentativas=1,
            erro_detalhe="Previous error",
        )
        mock_processamento_repository.buscar_por_analise_id.return_value = failed_processamento
        mock_processamento_repository.salvar_componentes.return_value = []
        mock_processamento_repository.salvar_riscos.return_value = []

        mock_file_storage.download_file.return_value = sample_image_bytes
        mock_image_processor.normalize.return_value = "base64"
        mock_analysis_pipeline.run.return_value = AnaliseResultSchema()

        use_case = ProcessDiagram(
            processamento_repository=mock_processamento_repository,
            event_publisher=mock_event_publisher,
            file_storage=mock_file_storage,
            image_processor=mock_image_processor,
            analysis_pipeline=mock_analysis_pipeline,
        )

        # Act
        await use_case.execute(str(analise_id), "diagrama.pdf", "application/pdf")

        # Assert
        # Should attempt again
        mock_file_storage.download_file.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_diagram_storage_download_error_retriable(
        self,
        analise_id: uuid.UUID,
        mock_processamento_repository,
        mock_event_publisher,
        mock_file_storage,
        mock_image_processor,
        mock_analysis_pipeline,
    ) -> None:
        """Test ProcessDiagram handles retriable StorageDownloadError."""
        # Arrange
        processamento = Processamento(analise_id=analise_id)
        mock_processamento_repository.buscar_por_analise_id.return_value = None
        mock_processamento_repository.salvar_processamento.return_value = processamento

        mock_file_storage.download_file.side_effect = StorageDownloadError("S3 connection timeout")

        use_case = ProcessDiagram(
            processamento_repository=mock_processamento_repository,
            event_publisher=mock_event_publisher,
            file_storage=mock_file_storage,
            image_processor=mock_image_processor,
            analysis_pipeline=mock_analysis_pipeline,
        )

        # Act
        await use_case.execute(str(analise_id), "diagrama.pdf", "application/pdf")

        # Assert
        # Should emit AnaliseFalhou event
        calls = [call for call in mock_event_publisher.publish_event.call_args_list]
        assert any("falhou" in str(call).lower() for call in calls)

    @pytest.mark.asyncio
    async def test_process_diagram_image_processing_error_non_retriable(
        self,
        analise_id: uuid.UUID,
        mock_processamento_repository,
        mock_event_publisher,
        mock_file_storage,
        mock_image_processor,
        mock_analysis_pipeline,
        sample_image_bytes,
    ) -> None:
        """Test ProcessDiagram handles non-retriable ImageProcessingError."""
        # Arrange
        processamento = Processamento(analise_id=analise_id)
        mock_processamento_repository.buscar_por_analise_id.return_value = None
        mock_processamento_repository.salvar_processamento.return_value = processamento

        mock_file_storage.download_file.return_value = sample_image_bytes
        mock_image_processor.normalize.side_effect = ImageProcessingError("Corrupted image")

        use_case = ProcessDiagram(
            processamento_repository=mock_processamento_repository,
            event_publisher=mock_event_publisher,
            file_storage=mock_file_storage,
            image_processor=mock_image_processor,
            analysis_pipeline=mock_analysis_pipeline,
        )

        # Act
        await use_case.execute(str(analise_id), "diagrama.pdf", "application/pdf")

        # Assert
        mock_event_publisher.publish_event.assert_called()

    @pytest.mark.asyncio
    async def test_process_diagram_llm_timeout_error_retriable(
        self,
        analise_id: uuid.UUID,
        mock_processamento_repository,
        mock_event_publisher,
        mock_file_storage,
        mock_image_processor,
        mock_analysis_pipeline,
        sample_image_bytes,
    ) -> None:
        """Test ProcessDiagram handles retriable LLMTimeoutError."""
        # Arrange
        processamento = Processamento(analise_id=analise_id)
        mock_processamento_repository.buscar_por_analise_id.return_value = None
        mock_processamento_repository.salvar_processamento.return_value = processamento

        mock_file_storage.download_file.return_value = sample_image_bytes
        mock_image_processor.normalize.return_value = "base64"
        mock_analysis_pipeline.run.side_effect = LLMTimeoutError("Request timeout")

        use_case = ProcessDiagram(
            processamento_repository=mock_processamento_repository,
            event_publisher=mock_event_publisher,
            file_storage=mock_file_storage,
            image_processor=mock_image_processor,
            analysis_pipeline=mock_analysis_pipeline,
        )

        # Act
        await use_case.execute(str(analise_id), "diagrama.pdf", "application/pdf")

        # Assert
        # Should emit failure event
        assert mock_event_publisher.publish_event.call_count >= 2

    @pytest.mark.asyncio
    async def test_process_diagram_llm_content_filter_error_non_retriable(
        self,
        analise_id: uuid.UUID,
        mock_processamento_repository,
        mock_event_publisher,
        mock_file_storage,
        mock_image_processor,
        mock_analysis_pipeline,
        sample_image_bytes,
    ) -> None:
        """Test ProcessDiagram handles non-retriable LLMContentFilterError."""
        # Arrange
        processamento = Processamento(analise_id=analise_id)
        mock_processamento_repository.buscar_por_analise_id.return_value = None
        mock_processamento_repository.salvar_processamento.return_value = processamento

        mock_file_storage.download_file.return_value = sample_image_bytes
        mock_image_processor.normalize.return_value = "base64"
        mock_analysis_pipeline.run.side_effect = LLMContentFilterError("Content filtered")

        use_case = ProcessDiagram(
            processamento_repository=mock_processamento_repository,
            event_publisher=mock_event_publisher,
            file_storage=mock_file_storage,
            image_processor=mock_image_processor,
            analysis_pipeline=mock_analysis_pipeline,
        )

        # Act
        await use_case.execute(str(analise_id), "diagrama.pdf", "application/pdf")

        # Assert
        assert mock_event_publisher.publish_event.call_count >= 2

    @pytest.mark.asyncio
    async def test_process_diagram_schema_validation_error(
        self,
        analise_id: uuid.UUID,
        mock_processamento_repository,
        mock_event_publisher,
        mock_file_storage,
        mock_image_processor,
        mock_analysis_pipeline,
        sample_image_bytes,
    ) -> None:
        """Test ProcessDiagram handles SchemaValidationError."""
        # Arrange
        processamento = Processamento(analise_id=analise_id)
        mock_processamento_repository.buscar_por_analise_id.return_value = None
        mock_processamento_repository.salvar_processamento.return_value = processamento

        mock_file_storage.download_file.return_value = sample_image_bytes
        mock_image_processor.normalize.return_value = "base64"
        mock_analysis_pipeline.run.side_effect = SchemaValidationError("Cannot parse schema")

        use_case = ProcessDiagram(
            processamento_repository=mock_processamento_repository,
            event_publisher=mock_event_publisher,
            file_storage=mock_file_storage,
            image_processor=mock_image_processor,
            analysis_pipeline=mock_analysis_pipeline,
        )

        # Act
        await use_case.execute(str(analise_id), "diagrama.pdf", "application/pdf")

        # Assert
        assert mock_event_publisher.publish_event.call_count >= 2

    @pytest.mark.asyncio
    async def test_process_diagram_sanity_check_failure(
        self,
        analise_id: uuid.UUID,
        mock_processamento_repository,
        mock_event_publisher,
        mock_file_storage,
        mock_image_processor,
        mock_analysis_pipeline,
        sample_image_bytes,
    ) -> None:
        """Test ProcessDiagram handles AnaliseInsanaError from sanity checks."""
        # Arrange
        processamento = Processamento(analise_id=analise_id)
        mock_processamento_repository.buscar_por_analise_id.return_value = None
        mock_processamento_repository.salvar_processamento.return_value = processamento

        # Create result with excessive components to fail sanity check
        excessive_componentes = [
            ComponenteSchema(
                nome=f"Component {i}",
                tipo=TipoComponente.SERVICE,
                confianca=0.95,
                metadata=ComponenteMetadata(descricao="Test"),
            )
            for i in range(35)  # Exceeds MAX_COMPONENTES=30
        ]
        result = AnaliseResultSchema(componentes=excessive_componentes)

        mock_file_storage.download_file.return_value = sample_image_bytes
        mock_image_processor.normalize.return_value = "base64"
        mock_analysis_pipeline.run.return_value = result

        use_case = ProcessDiagram(
            processamento_repository=mock_processamento_repository,
            event_publisher=mock_event_publisher,
            file_storage=mock_file_storage,
            image_processor=mock_image_processor,
            analysis_pipeline=mock_analysis_pipeline,
        )

        # Act
        await use_case.execute(str(analise_id), "diagrama.pdf", "application/pdf")

        # Assert
        # Should fail and emit AnaliseFalhou
        assert mock_event_publisher.publish_event.call_count >= 2


class TestGetProcessingResult:
    """Tests for the GetProcessingResult use case."""

    @pytest.mark.asyncio
    async def test_get_processing_result_success(
        self,
        analise_id: uuid.UUID,
        processamento_id: uuid.UUID,
        componente_id: uuid.UUID,
        risco_id: uuid.UUID,
        mock_processamento_repository,
    ) -> None:
        """Test GetProcessingResult returns complete result."""
        # Arrange
        processamento = Processamento(
            id=processamento_id,
            analise_id=analise_id,
            status=StatusProcessamento.CONCLUIDO,
        )
        componentes = [
            Componente(
                id=componente_id,
                processamento_id=processamento_id,
                nome="API Gateway",
                tipo="api_gateway",
                confianca=0.95,
                metadata={"descricao": "API"},
            ),
        ]
        riscos = [
            Risco(
                id=risco_id,
                processamento_id=processamento_id,
                descricao="Single point of failure",
                severidade="alta",
                recomendacao_descricao="Implement redundancy",
                recomendacao_prioridade="alta",
                componentes_afetados=["API Gateway"],
            ),
        ]

        mock_processamento_repository.buscar_resultado_completo.return_value = (
            processamento,
            componentes,
            riscos,
        )

        use_case = GetProcessingResult(
            processamento_repository=mock_processamento_repository,
        )

        # Act
        result = await use_case.execute(analise_id)

        # Assert
        assert result.analise_id == analise_id
        assert result.status == "concluido"
        assert len(result.componentes) == 1
        assert len(result.riscos) == 1
        assert result.componentes[0].nome == "API Gateway"

    @pytest.mark.asyncio
    async def test_get_processing_result_not_found(
        self,
        analise_id: uuid.UUID,
        mock_processamento_repository,
    ) -> None:
        """Test GetProcessingResult raises error when processamento not found."""
        # Arrange
        mock_processamento_repository.buscar_resultado_completo.return_value = (None, [], [])

        use_case = GetProcessingResult(
            processamento_repository=mock_processamento_repository,
        )

        # Act & Assert
        with pytest.raises(ProcessamentoNaoEncontradoError):
            await use_case.execute(analise_id)

    @pytest.mark.asyncio
    async def test_get_processing_result_pending_status(
        self,
        analise_id: uuid.UUID,
        processamento_id: uuid.UUID,
        mock_processamento_repository,
    ) -> None:
        """Test GetProcessingResult with pending processamento."""
        # Arrange
        processamento = Processamento(
            id=processamento_id,
            analise_id=analise_id,
            status=StatusProcessamento.PENDENTE,
        )
        mock_processamento_repository.buscar_resultado_completo.return_value = (
            processamento,
            [],
            [],
        )

        use_case = GetProcessingResult(
            processamento_repository=mock_processamento_repository,
        )

        # Act
        result = await use_case.execute(analise_id)

        # Assert
        assert result.status == "pendente"
        assert result.componentes == []
        assert result.riscos == []

    @pytest.mark.asyncio
    async def test_get_processing_result_error_status(
        self,
        analise_id: uuid.UUID,
        processamento_id: uuid.UUID,
        mock_processamento_repository,
    ) -> None:
        """Test GetProcessingResult with error processamento."""
        # Arrange
        processamento = Processamento(
            id=processamento_id,
            analise_id=analise_id,
            status=StatusProcessamento.ERRO,
            erro_detalhe="LLM timeout",
        )
        mock_processamento_repository.buscar_resultado_completo.return_value = (
            processamento,
            [],
            [],
        )

        use_case = GetProcessingResult(
            processamento_repository=mock_processamento_repository,
        )

        # Act
        result = await use_case.execute(analise_id)

        # Assert
        assert result.status == "erro"
