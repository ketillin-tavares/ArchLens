import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dtos import RelatorioResponse
from src.application.use_cases import GetReport
from src.infrastructure.database import get_session
from src.interface.gateways.relatorio_repository_gateway import SQLAlchemyRelatorioRepository
from src.interface.presenters.error_presenter import NotFoundResponse

router = APIRouter(prefix="/relatorios", tags=["v1"])


@router.get(
    "/{analise_id}",
    response_model=RelatorioResponse,
    responses={404: {"model": NotFoundResponse}},
)
async def get_report(
    analise_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> RelatorioResponse:
    """Consulta o relatório gerado para uma análise pelo ID da análise."""
    use_case = GetReport(
        relatorio_repository=SQLAlchemyRelatorioRepository(session),
    )

    return await use_case.execute(analise_id)
