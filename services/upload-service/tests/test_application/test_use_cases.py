"""Tests for application use cases with mocked ports."""

import asyncio
import uuid
from unittest.mock import AsyncMock

import pytest

from src.application.dtos import AnaliseResponse, DiagramaUploadResponse
from src.application.use_cases import GetAnalysisStatus, HandleStatusUpdate, SubmitDiagram
from src.domain.entities import Analise, Diagrama
from src.domain.exceptions import AnaliseNaoEncontradaError, ArquivoInvalidoError, ArquivoTamanhoExcedidoError
from src.domain.value_objects import ArquivoDiagrama, StatusAnalise


class TestSubmitDiagram:
    """Tests for SubmitDiagram use case."""

    @pytest.fixture
    def mocked_ports(self):
        """Create mocked port implementations."""
        return {
            "diagrama_repository": AsyncMock(),
            "analise_repository": AsyncMock(),
            "file_storage": AsyncMock(),
            "event_publisher": AsyncMock(),
        }

    def test_submit_diagram_happy_path(self, mocked_ports) -> None:
        """Test successful diagram submission flow."""
        # Arrange
        conteudo = b"fake_png_data"
        arquivo = ArquivoDiagrama(
            nome_original="arquitetura.png",
            content_type="image/png",
            tamanho_bytes=len(conteudo),
            conteudo=conteudo,
        )

        # Mock repository responses
        diagrama_salvo = Diagrama(
            id=uuid.uuid4(),
            nome_original=arquivo.nome_original,
            content_type=arquivo.content_type,
            tamanho_bytes=arquivo.tamanho_bytes,
            storage_path="diagramas/2026/03/30/uuid.png",
        )

        analise_salva = Analise(
            id=uuid.uuid4(),
            diagrama_id=diagrama_salvo.id,
            status=StatusAnalise.RECEBIDO,
        )

        mocked_ports["diagrama_repository"].salvar.return_value = diagrama_salvo
        mocked_ports["analise_repository"].salvar.return_value = analise_salva
        mocked_ports["file_storage"].upload_file.return_value = diagrama_salvo.storage_path
        mocked_ports["event_publisher"].publish_event.return_value = None

        use_case = SubmitDiagram(
            diagrama_repository=mocked_ports["diagrama_repository"],
            analise_repository=mocked_ports["analise_repository"],
            file_storage=mocked_ports["file_storage"],
            event_publisher=mocked_ports["event_publisher"],
        )

        # Act
        result = asyncio.run(use_case.execute(arquivo))

        # Assert
        assert isinstance(result, DiagramaUploadResponse)
        assert result.analise_id == analise_salva.id
        assert result.status == StatusAnalise.RECEBIDO.value
        assert result.criado_em == analise_salva.criado_em

        # Verify file storage was called
        mocked_ports["file_storage"].upload_file.assert_called_once()
        call_args = mocked_ports["file_storage"].upload_file.call_args
        assert call_args.kwargs["file_bytes"] == conteudo
        assert call_args.kwargs["content_type"] == "image/png"

        # Verify repositories were called
        mocked_ports["diagrama_repository"].salvar.assert_called_once()
        mocked_ports["analise_repository"].salvar.assert_called_once()

        # Verify event publisher was called
        mocked_ports["event_publisher"].publish_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_submit_diagram_rejects_invalid_file_type(self, mocked_ports) -> None:
        """Test that SubmitDiagram raises ArquivoInvalidoError for unsupported types."""
        # Arrange
        conteudo = b"fake_doc_data"
        arquivo = ArquivoDiagrama(
            nome_original="documento.docx",
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            tamanho_bytes=len(conteudo),
            conteudo=conteudo,
        )

        use_case = SubmitDiagram(
            diagrama_repository=mocked_ports["diagrama_repository"],
            analise_repository=mocked_ports["analise_repository"],
            file_storage=mocked_ports["file_storage"],
            event_publisher=mocked_ports["event_publisher"],
        )

        # Act & Assert
        with pytest.raises(ArquivoInvalidoError):
            await use_case.execute(arquivo)

        # Verify no repositories were accessed
        mocked_ports["diagrama_repository"].salvar.assert_not_called()
        mocked_ports["analise_repository"].salvar.assert_not_called()
        mocked_ports["file_storage"].upload_file.assert_not_called()

    @pytest.mark.asyncio
    async def test_submit_diagram_rejects_oversized_file(self, mocked_ports) -> None:
        """Test that SubmitDiagram raises ArquivoTamanhoExcedidoError for large files."""
        # Arrange
        tamanho_maximo = 10 * 1024 * 1024  # 10MB
        tamanho_excedido = tamanho_maximo + 1
        conteudo = b"x" * tamanho_excedido

        arquivo = ArquivoDiagrama(
            nome_original="grande.png",
            content_type="image/png",
            tamanho_bytes=tamanho_excedido,
            conteudo=conteudo,
        )

        use_case = SubmitDiagram(
            diagrama_repository=mocked_ports["diagrama_repository"],
            analise_repository=mocked_ports["analise_repository"],
            file_storage=mocked_ports["file_storage"],
            event_publisher=mocked_ports["event_publisher"],
        )

        # Act & Assert
        with pytest.raises(ArquivoTamanhoExcedidoError):
            await use_case.execute(arquivo)

        # Verify no repositories were accessed
        mocked_ports["diagrama_repository"].salvar.assert_not_called()

    @pytest.mark.asyncio
    async def test_submit_diagram_accepts_valid_png(self, mocked_ports) -> None:
        """Test successful submission with PNG file."""
        # Arrange
        conteudo = b"fake_png_data"
        arquivo = ArquivoDiagrama(
            nome_original="arquitetura.png",
            content_type="image/png",
            tamanho_bytes=len(conteudo),
            conteudo=conteudo,
        )

        diagrama_salvo = Diagrama(
            id=uuid.uuid4(),
            nome_original=arquivo.nome_original,
            content_type=arquivo.content_type,
            tamanho_bytes=arquivo.tamanho_bytes,
            storage_path="diagramas/2026/03/30/uuid.png",
        )

        analise_salva = Analise(
            id=uuid.uuid4(),
            diagrama_id=diagrama_salvo.id,
            status=StatusAnalise.RECEBIDO,
        )

        mocked_ports["diagrama_repository"].salvar.return_value = diagrama_salvo
        mocked_ports["analise_repository"].salvar.return_value = analise_salva
        mocked_ports["file_storage"].upload_file.return_value = diagrama_salvo.storage_path

        use_case = SubmitDiagram(
            diagrama_repository=mocked_ports["diagrama_repository"],
            analise_repository=mocked_ports["analise_repository"],
            file_storage=mocked_ports["file_storage"],
            event_publisher=mocked_ports["event_publisher"],
        )

        # Act
        result = await use_case.execute(arquivo)

        # Assert
        assert result.analise_id == analise_salva.id
        assert result.status == StatusAnalise.RECEBIDO.value

    @pytest.mark.asyncio
    async def test_submit_diagram_accepts_valid_jpeg(self, mocked_ports) -> None:
        """Test successful submission with JPEG file."""
        # Arrange
        conteudo = b"fake_jpeg_data"
        arquivo = ArquivoDiagrama(
            nome_original="arquitetura.jpg",
            content_type="image/jpeg",
            tamanho_bytes=len(conteudo),
            conteudo=conteudo,
        )

        diagrama_salvo = Diagrama(
            id=uuid.uuid4(),
            nome_original=arquivo.nome_original,
            content_type=arquivo.content_type,
            tamanho_bytes=arquivo.tamanho_bytes,
            storage_path="diagramas/2026/03/30/uuid.jpeg",
        )

        analise_salva = Analise(
            id=uuid.uuid4(),
            diagrama_id=diagrama_salvo.id,
            status=StatusAnalise.RECEBIDO,
        )

        mocked_ports["diagrama_repository"].salvar.return_value = diagrama_salvo
        mocked_ports["analise_repository"].salvar.return_value = analise_salva
        mocked_ports["file_storage"].upload_file.return_value = diagrama_salvo.storage_path

        use_case = SubmitDiagram(
            diagrama_repository=mocked_ports["diagrama_repository"],
            analise_repository=mocked_ports["analise_repository"],
            file_storage=mocked_ports["file_storage"],
            event_publisher=mocked_ports["event_publisher"],
        )

        # Act
        result = await use_case.execute(arquivo)

        # Assert
        assert result.analise_id == analise_salva.id

    @pytest.mark.asyncio
    async def test_submit_diagram_publishes_event(self, mocked_ports) -> None:
        """Test that SubmitDiagram publishes DiagramaEnviado event."""
        # Arrange
        conteudo = b"fake_pdf_data"
        arquivo = ArquivoDiagrama(
            nome_original="arquitetura.pdf",
            content_type="application/pdf",
            tamanho_bytes=len(conteudo),
            conteudo=conteudo,
        )

        diagrama_salvo = Diagrama(
            id=uuid.uuid4(),
            nome_original=arquivo.nome_original,
            content_type=arquivo.content_type,
            tamanho_bytes=arquivo.tamanho_bytes,
            storage_path="diagramas/2026/03/30/uuid.pdf",
        )

        analise_salva = Analise(
            id=uuid.uuid4(),
            diagrama_id=diagrama_salvo.id,
            status=StatusAnalise.RECEBIDO,
        )

        mocked_ports["diagrama_repository"].salvar.return_value = diagrama_salvo
        mocked_ports["analise_repository"].salvar.return_value = analise_salva
        mocked_ports["file_storage"].upload_file.return_value = diagrama_salvo.storage_path

        use_case = SubmitDiagram(
            diagrama_repository=mocked_ports["diagrama_repository"],
            analise_repository=mocked_ports["analise_repository"],
            file_storage=mocked_ports["file_storage"],
            event_publisher=mocked_ports["event_publisher"],
        )

        # Act
        await use_case.execute(arquivo)

        # Assert
        mocked_ports["event_publisher"].publish_event.assert_called_once()
        call_args = mocked_ports["event_publisher"].publish_event.call_args
        assert call_args.kwargs["event_type"] == "DiagramaEnviado"
        assert call_args.kwargs["routing_key"] == "analise.diagrama.enviado"
        assert "payload" in call_args.kwargs


class TestGetAnalysisStatus:
    """Tests for GetAnalysisStatus use case."""

    @pytest.mark.asyncio
    async def test_get_analysis_status_happy_path(self) -> None:
        """Test successful retrieval of analysis status."""
        # Arrange
        analise_id = uuid.uuid4()
        diagrama_id = uuid.uuid4()
        analise = Analise(
            id=analise_id,
            diagrama_id=diagrama_id,
            status=StatusAnalise.EM_PROCESSAMENTO,
        )

        mock_repo = AsyncMock()
        mock_repo.buscar_por_id.return_value = analise

        use_case = GetAnalysisStatus(analise_repository=mock_repo)

        # Act
        result = await use_case.execute(analise_id)

        # Assert
        assert isinstance(result, AnaliseResponse)
        assert result.id == analise_id
        assert result.diagrama_id == diagrama_id
        assert result.status == StatusAnalise.EM_PROCESSAMENTO.value
        mock_repo.buscar_por_id.assert_called_once_with(analise_id)

    @pytest.mark.asyncio
    async def test_get_analysis_status_not_found(self) -> None:
        """Test that AnaliseNaoEncontradaError is raised when not found."""
        # Arrange
        analise_id = uuid.uuid4()

        mock_repo = AsyncMock()
        mock_repo.buscar_por_id.return_value = None

        use_case = GetAnalysisStatus(analise_repository=mock_repo)

        # Act & Assert
        with pytest.raises(AnaliseNaoEncontradaError):
            await use_case.execute(analise_id)

    @pytest.mark.asyncio
    async def test_get_analysis_status_with_error_details(self) -> None:
        """Test retrieval of analysis status with error details."""
        # Arrange
        analise_id = uuid.uuid4()
        diagrama_id = uuid.uuid4()
        erro_detalhe = "Diagrama possui estrutura inválida"

        analise = Analise(
            id=analise_id,
            diagrama_id=diagrama_id,
            status=StatusAnalise.ERRO,
            erro_detalhe=erro_detalhe,
        )

        mock_repo = AsyncMock()
        mock_repo.buscar_por_id.return_value = analise

        use_case = GetAnalysisStatus(analise_repository=mock_repo)

        # Act
        result = await use_case.execute(analise_id)

        # Assert
        assert result.status == StatusAnalise.ERRO.value
        assert result.erro_detalhe == erro_detalhe

    @pytest.mark.asyncio
    async def test_get_analysis_status_recebido(self) -> None:
        """Test retrieval of newly received analysis."""
        # Arrange
        analise_id = uuid.uuid4()
        diagrama_id = uuid.uuid4()

        analise = Analise(
            id=analise_id,
            diagrama_id=diagrama_id,
            status=StatusAnalise.RECEBIDO,
        )

        mock_repo = AsyncMock()
        mock_repo.buscar_por_id.return_value = analise

        use_case = GetAnalysisStatus(analise_repository=mock_repo)

        # Act
        result = await use_case.execute(analise_id)

        # Assert
        assert result.status == StatusAnalise.RECEBIDO.value
        assert result.erro_detalhe is None

    @pytest.mark.asyncio
    async def test_get_analysis_status_analisado(self) -> None:
        """Test retrieval of completed analysis."""
        # Arrange
        analise_id = uuid.uuid4()
        diagrama_id = uuid.uuid4()

        analise = Analise(
            id=analise_id,
            diagrama_id=diagrama_id,
            status=StatusAnalise.ANALISADO,
        )

        mock_repo = AsyncMock()
        mock_repo.buscar_por_id.return_value = analise

        use_case = GetAnalysisStatus(analise_repository=mock_repo)

        # Act
        result = await use_case.execute(analise_id)

        # Assert
        assert result.status == StatusAnalise.ANALISADO.value


class TestHandleStatusUpdate:
    """Tests for HandleStatusUpdate use case."""

    @pytest.mark.asyncio
    async def test_handle_status_update_valid_transition(self) -> None:
        """Test valid status update from event."""
        # Arrange
        analise_id = uuid.uuid4()

        mock_repo = AsyncMock()
        mock_repo.atualizar_status.return_value = True

        use_case = HandleStatusUpdate(analise_repository=mock_repo)

        # Act
        await use_case.execute(
            analise_id=str(analise_id),
            novo_status="em_processamento",
        )

        # Assert
        mock_repo.atualizar_status.assert_called_once()
        call_args = mock_repo.atualizar_status.call_args
        assert call_args.args[0] == analise_id
        assert call_args.args[1] == StatusAnalise.EM_PROCESSAMENTO

    @pytest.mark.asyncio
    async def test_handle_status_update_with_error_details(self) -> None:
        """Test status update with error details."""
        # Arrange
        analise_id = uuid.uuid4()
        erro_detalhe = "Diagrama inválido"

        mock_repo = AsyncMock()
        mock_repo.atualizar_status.return_value = True

        use_case = HandleStatusUpdate(analise_repository=mock_repo)

        # Act
        await use_case.execute(
            analise_id=str(analise_id),
            novo_status="erro",
            erro_detalhe=erro_detalhe,
        )

        # Assert
        mock_repo.atualizar_status.assert_called_once()
        call_args = mock_repo.atualizar_status.call_args
        # The error_detalhe is passed as the third positional argument
        assert call_args.args[2] == erro_detalhe

    @pytest.mark.asyncio
    async def test_handle_status_update_idempotent_skip(self) -> None:
        """Test idempotent behavior when transition is invalid."""
        # Arrange
        analise_id = uuid.uuid4()

        mock_repo = AsyncMock()
        mock_repo.atualizar_status.return_value = False

        use_case = HandleStatusUpdate(analise_repository=mock_repo)

        # Act
        await use_case.execute(
            analise_id=str(analise_id),
            novo_status="recebido",
        )

        # Assert
        mock_repo.atualizar_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_status_update_invalid_uuid(self) -> None:
        """Test handling of invalid UUID format."""
        # Arrange
        mock_repo = AsyncMock()
        use_case = HandleStatusUpdate(analise_repository=mock_repo)

        # Act
        await use_case.execute(
            analise_id="invalid-uuid",
            novo_status="em_processamento",
        )

        # Assert
        mock_repo.atualizar_status.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_status_update_invalid_status(self) -> None:
        """Test handling of invalid status value."""
        # Arrange
        analise_id = uuid.uuid4()
        mock_repo = AsyncMock()
        use_case = HandleStatusUpdate(analise_repository=mock_repo)

        # Act
        await use_case.execute(
            analise_id=str(analise_id),
            novo_status="status_invalido",
        )

        # Assert
        mock_repo.atualizar_status.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_status_update_analisado(self) -> None:
        """Test updating to ANALISADO status."""
        # Arrange
        analise_id = uuid.uuid4()

        mock_repo = AsyncMock()
        mock_repo.atualizar_status.return_value = True

        use_case = HandleStatusUpdate(analise_repository=mock_repo)

        # Act
        await use_case.execute(
            analise_id=str(analise_id),
            novo_status="analisado",
        )

        # Assert
        mock_repo.atualizar_status.assert_called_once()
        call_args = mock_repo.atualizar_status.call_args
        assert call_args.args[1] == StatusAnalise.ANALISADO
