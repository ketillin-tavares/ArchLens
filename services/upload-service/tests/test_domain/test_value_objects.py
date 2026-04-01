"""Tests for domain value objects."""

import pytest
from pydantic import ValidationError

from src.domain.exceptions import ArquivoInvalidoError, ArquivoTamanhoExcedidoError
from src.domain.value_objects import ArquivoDiagrama, StatusAnalise


class TestStatusAnalise:
    """Tests for StatusAnalise enum and its transitions."""

    def test_ordem_returns_correct_progression(self) -> None:
        """Verify that ordem() returns correct status progression order."""
        # Arrange
        ordem = StatusAnalise.ordem()

        # Act & Assert
        assert ordem[StatusAnalise.RECEBIDO] == 0
        assert ordem[StatusAnalise.EM_PROCESSAMENTO] == 1
        assert ordem[StatusAnalise.ANALISADO] == 2
        assert ordem[StatusAnalise.ERRO] == 2

    def test_pode_transitar_para_recebido_to_em_processamento(self) -> None:
        """Test valid transition from RECEBIDO to EM_PROCESSAMENTO."""
        # Arrange
        status_atual = StatusAnalise.RECEBIDO

        # Act
        pode_transitar = status_atual.pode_transitar_para(StatusAnalise.EM_PROCESSAMENTO)

        # Assert
        assert pode_transitar is True

    def test_pode_transitar_para_em_processamento_to_analisado(self) -> None:
        """Test valid transition from EM_PROCESSAMENTO to ANALISADO."""
        # Arrange
        status_atual = StatusAnalise.EM_PROCESSAMENTO

        # Act
        pode_transitar = status_atual.pode_transitar_para(StatusAnalise.ANALISADO)

        # Assert
        assert pode_transitar is True

    def test_pode_transitar_para_em_processamento_to_erro(self) -> None:
        """Test valid transition from EM_PROCESSAMENTO to ERRO."""
        # Arrange
        status_atual = StatusAnalise.EM_PROCESSAMENTO

        # Act
        pode_transitar = status_atual.pode_transitar_para(StatusAnalise.ERRO)

        # Assert
        assert pode_transitar is True

    def test_pode_transitar_para_recebido_to_erro(self) -> None:
        """Test valid transition from RECEBIDO to ERRO (skipping EM_PROCESSAMENTO)."""
        # Arrange
        status_atual = StatusAnalise.RECEBIDO

        # Act
        pode_transitar = status_atual.pode_transitar_para(StatusAnalise.ERRO)

        # Assert
        assert pode_transitar is True

    def test_pode_transitar_para_rejects_regression(self) -> None:
        """Test that regressing from ANALISADO to EM_PROCESSAMENTO is rejected."""
        # Arrange
        status_atual = StatusAnalise.ANALISADO

        # Act
        pode_transitar = status_atual.pode_transitar_para(StatusAnalise.EM_PROCESSAMENTO)

        # Assert
        assert pode_transitar is False

    def test_pode_transitar_para_same_status(self) -> None:
        """Test that transitioning to the same status is rejected."""
        # Arrange
        status_atual = StatusAnalise.RECEBIDO

        # Act
        pode_transitar = status_atual.pode_transitar_para(StatusAnalise.RECEBIDO)

        # Assert
        assert pode_transitar is False

    def test_pode_transitar_para_analisado_to_erro(self) -> None:
        """Test that transition from ANALISADO to ERRO is rejected (same order level)."""
        # Arrange
        status_atual = StatusAnalise.ANALISADO

        # Act
        pode_transitar = status_atual.pode_transitar_para(StatusAnalise.ERRO)

        # Assert
        assert pode_transitar is False


class TestArquivoDiagrama:
    """Tests for ArquivoDiagrama value object."""

    def test_create_valid_arquivo_png(self) -> None:
        """Test creating a valid PNG file."""
        # Arrange
        conteudo = b"fake_png_data"

        # Act
        arquivo = ArquivoDiagrama(
            nome_original="diagrama.png",
            content_type="image/png",
            tamanho_bytes=len(conteudo),
            conteudo=conteudo,
        )

        # Assert
        assert arquivo.nome_original == "diagrama.png"
        assert arquivo.content_type == "image/png"
        assert arquivo.tamanho_bytes == len(conteudo)
        assert arquivo.conteudo == conteudo

    def test_create_valid_arquivo_jpeg(self) -> None:
        """Test creating a valid JPEG file."""
        # Arrange
        conteudo = b"fake_jpeg_data"

        # Act
        arquivo = ArquivoDiagrama(
            nome_original="diagrama.jpg",
            content_type="image/jpeg",
            tamanho_bytes=len(conteudo),
            conteudo=conteudo,
        )

        # Assert
        assert arquivo.nome_original == "diagrama.jpg"
        assert arquivo.content_type == "image/jpeg"

    def test_create_valid_arquivo_pdf(self) -> None:
        """Test creating a valid PDF file."""
        # Arrange
        conteudo = b"fake_pdf_data"

        # Act
        arquivo = ArquivoDiagrama(
            nome_original="diagrama.pdf",
            content_type="application/pdf",
            tamanho_bytes=len(conteudo),
            conteudo=conteudo,
        )

        # Assert
        assert arquivo.nome_original == "diagrama.pdf"
        assert arquivo.content_type == "application/pdf"

    def test_validar_rejects_invalid_file_type(self) -> None:
        """Test that validar() rejects unsupported file types."""
        # Arrange
        conteudo = b"fake_doc_data"
        arquivo = ArquivoDiagrama(
            nome_original="documento.docx",
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            tamanho_bytes=len(conteudo),
            conteudo=conteudo,
        )

        # Act & Assert
        with pytest.raises(ArquivoInvalidoError) as exc_info:
            arquivo.validar()

        assert "Tipo de arquivo não suportado" in str(exc_info.value)

    def test_validar_rejects_oversized_file(self) -> None:
        """Test that validar() rejects files exceeding max size."""
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

        # Act & Assert
        with pytest.raises(ArquivoTamanhoExcedidoError) as exc_info:
            arquivo.validar()

        assert "tamanho máximo de 10MB" in str(exc_info.value)

    def test_validar_accepts_max_size(self) -> None:
        """Test that validar() accepts files at exactly max size."""
        # Arrange
        tamanho_maximo = 10 * 1024 * 1024  # 10MB
        conteudo = b"x" * tamanho_maximo

        arquivo = ArquivoDiagrama(
            nome_original="maxsize.png",
            content_type="image/png",
            tamanho_bytes=tamanho_maximo,
            conteudo=conteudo,
        )

        # Act & Assert
        arquivo.validar()  # Should not raise

    def test_validar_accepts_valid_arquivo(self) -> None:
        """Test that validar() passes for valid files."""
        # Arrange
        conteudo = b"fake_png_data"
        arquivo = ArquivoDiagrama(
            nome_original="diagrama.png",
            content_type="image/png",
            tamanho_bytes=len(conteudo),
            conteudo=conteudo,
        )

        # Act & Assert
        arquivo.validar()  # Should not raise

    def test_extensao_png(self) -> None:
        """Test extensao property for PNG."""
        # Arrange
        arquivo = ArquivoDiagrama(
            nome_original="diagrama.png",
            content_type="image/png",
            tamanho_bytes=10,
            conteudo=b"fake",
        )

        # Act
        ext = arquivo.extensao

        # Assert
        assert ext == "png"

    def test_extensao_jpeg(self) -> None:
        """Test extensao property for JPEG."""
        # Arrange
        arquivo = ArquivoDiagrama(
            nome_original="diagrama.jpeg",
            content_type="image/jpeg",
            tamanho_bytes=10,
            conteudo=b"fake",
        )

        # Act
        ext = arquivo.extensao

        # Assert
        assert ext == "jpeg"

    def test_extensao_pdf(self) -> None:
        """Test extensao property for PDF."""
        # Arrange
        arquivo = ArquivoDiagrama(
            nome_original="diagrama.pdf",
            content_type="application/pdf",
            tamanho_bytes=10,
            conteudo=b"fake",
        )

        # Act
        ext = arquivo.extensao

        # Assert
        assert ext == "pdf"

    def test_tamanho_bytes_validation(self) -> None:
        """Test that tamanho_bytes must be greater than 0."""
        # Act & Assert
        with pytest.raises(ValidationError):
            ArquivoDiagrama(
                nome_original="vazio.png",
                content_type="image/png",
                tamanho_bytes=0,
                conteudo=b"",
            )

    def test_conteudo_excluded_from_model_dump(self) -> None:
        """Test that conteudo is excluded from model_dump()."""
        # Arrange
        conteudo = b"fake_data"
        arquivo = ArquivoDiagrama(
            nome_original="diagrama.png",
            content_type="image/png",
            tamanho_bytes=len(conteudo),
            conteudo=conteudo,
        )

        # Act
        dumped = arquivo.model_dump()

        # Assert
        assert "conteudo" not in dumped
        assert "nome_original" in dumped
        assert "content_type" in dumped
        assert "tamanho_bytes" in dumped
