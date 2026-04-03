import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dtos import ProcessamentoResponse
from src.application.use_cases import GetProcessingResult
from src.infrastructure.database import get_session
from src.interface.gateways.processamento_repository_gateway import SQLAlchemyProcessamentoRepository
from src.interface.presenters.error_presenter import NotFoundResponse

router = APIRouter(prefix="/processamentos", tags=["v1"])


@router.get(
    "/{analise_id}",
    response_model=ProcessamentoResponse,
    responses={404: {"model": NotFoundResponse}},
)
async def get_processing_result(
    analise_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> ProcessamentoResponse:
    """Consulta o resultado de processamento para uma análise pelo ID."""
    use_case = GetProcessingResult(
        processamento_repository=SQLAlchemyProcessamentoRepository(session),
    )

    return await use_case.execute(analise_id)
