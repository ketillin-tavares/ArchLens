import uuid

from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dtos import AnaliseResponse, DiagramaUploadResponse, DownloadRelatorioResponse
from src.application.use_cases import DownloadRelatorio, GetAnalysisStatus, RetryAnalysis, SubmitDiagram
from src.domain.value_objects import ArquivoDiagrama
from src.infrastructure.database import get_session
from src.infrastructure.messaging.shared import rabbitmq_publisher
from src.interface.gateways.analise_repository_gateway import SQLAlchemyAnaliseRepository
from src.interface.gateways.diagrama_repository_gateway import SQLAlchemyDiagramaRepository
from src.interface.gateways.event_publisher_gateway import RabbitMQEventPublisherGateway
from src.interface.gateways.file_storage_gateway import S3FileStorageGateway
from src.interface.presenters.error_presenter import (
    ArquivoInvalidoResponse,
    ArquivoTamanhoExcedidoResponse,
    ConflictResponse,
    NotFoundResponse,
)

router = APIRouter(prefix="/analises", tags=["v1"])


def _get_publisher_gateway() -> RabbitMQEventPublisherGateway:
    """Obtém o gateway do publisher RabbitMQ usando a instância global."""
    return RabbitMQEventPublisherGateway(publisher=rabbitmq_publisher)


@router.post(
    "",
    response_model=DiagramaUploadResponse,
    status_code=202,
    responses={
        400: {"model": ArquivoInvalidoResponse},
        413: {"model": ArquivoTamanhoExcedidoResponse},
    },
)
async def submit_diagram(
    file: UploadFile,
    session: AsyncSession = Depends(get_session),
) -> DiagramaUploadResponse:
    """
    Recebe um diagrama de arquitetura via upload e inicia o fluxo de análise.

    Aceita arquivos image/png, image/jpeg ou application/pdf com tamanho máximo de 10MB.
    """
    conteudo = await file.read()

    arquivo = ArquivoDiagrama(
        nome_original=file.filename or "sem_nome",
        content_type=file.content_type or "application/octet-stream",
        tamanho_bytes=len(conteudo),
        conteudo=conteudo,
    )

    use_case = SubmitDiagram(
        diagrama_repository=SQLAlchemyDiagramaRepository(session),
        analise_repository=SQLAlchemyAnaliseRepository(session),
        file_storage=S3FileStorageGateway(),
        event_publisher=_get_publisher_gateway(),
    )

    return await use_case.execute(arquivo)


@router.get(
    "/{analise_id}",
    response_model=AnaliseResponse,
    responses={404: {"model": NotFoundResponse}},
)
async def get_analysis_status(
    analise_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> AnaliseResponse:
    """Consulta o status de uma análise pelo ID."""
    use_case = GetAnalysisStatus(
        analise_repository=SQLAlchemyAnaliseRepository(session),
    )

    return await use_case.execute(analise_id)


@router.get(
    "/{analise_id}/relatorio/download",
    response_model=DownloadRelatorioResponse,
    responses={
        404: {"model": NotFoundResponse},
        409: {"model": ConflictResponse},
    },
)
async def download_relatorio(
    analise_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> DownloadRelatorioResponse:
    """
    Gera URL pré-assinada para download do relatório Markdown de uma análise concluída.

    A análise deve estar com status 'analisado' e ter um relatório disponível no S3.
    A URL gerada expira em 3600 segundos.
    """
    use_case = DownloadRelatorio(
        analise_repository=SQLAlchemyAnaliseRepository(session),
        file_storage=S3FileStorageGateway(),
    )

    return await use_case.execute(analise_id)


@router.post(
    "/{analise_id}/retry",
    response_model=AnaliseResponse,
    status_code=202,
    responses={
        404: {"model": NotFoundResponse},
        409: {"model": ConflictResponse},
    },
)
async def retry_analysis(
    analise_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> AnaliseResponse:
    """Retenta o processamento de uma análise que falhou."""
    use_case = RetryAnalysis(
        analise_repository=SQLAlchemyAnaliseRepository(session),
        diagrama_repository=SQLAlchemyDiagramaRepository(session),
        event_publisher=_get_publisher_gateway(),
    )

    return await use_case.execute(analise_id)
