import uuid

from src.application.dtos import AnaliseResponse
from src.domain.exceptions import AnaliseNaoEncontradaError
from src.domain.repositories import AnaliseRepository


class GetAnalysisStatus:
    """Caso de uso para consulta de status de uma análise."""

    def __init__(self, analise_repository: AnaliseRepository) -> None:
        self._analise_repo = analise_repository

    async def execute(self, analise_id: uuid.UUID) -> AnaliseResponse:
        """
        Busca o status de uma análise pelo ID.

        Args:
            analise_id: UUID da análise.

        Returns:
            DTO com os dados da análise.

        Raises:
            AnaliseNaoEncontradaError: Se a análise não existe.
        """
        analise = await self._analise_repo.buscar_por_id(analise_id)
        if analise is None:
            raise AnaliseNaoEncontradaError("Análise não encontrada")

        return AnaliseResponse(
            id=analise.id,
            diagrama_id=analise.diagrama_id,
            status=analise.status.value,
            erro_detalhe=analise.erro_detalhe,
            criado_em=analise.criado_em,
            atualizado_em=analise.atualizado_em,
        )
