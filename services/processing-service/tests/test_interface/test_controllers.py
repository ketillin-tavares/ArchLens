"""Unit tests for controllers."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app


class TestProcessamentoController:
    """Tests for processamento controller endpoints."""

    @pytest.mark.asyncio
    async def test_get_processamento_success(self) -> None:
        """Test GET /api/v1/processamentos/{analise_id} returns result."""
        # Arrange
        analise_id = uuid.uuid4()
        transport = ASGITransport(app=app)

        mock_response_dto = {
            "analise_id": str(analise_id),
            "status": "concluido",
            "iniciado_em": "2026-04-02T10:00:00+00:00",
            "concluido_em": "2026-04-02T10:05:00+00:00",
            "componentes": [
                {
                    "id": str(uuid.uuid4()),
                    "nome": "API Gateway",
                    "tipo": "api_gateway",
                    "confianca": 0.95,
                    "metadata": {"descricao": "API"},
                }
            ],
            "riscos": [
                {
                    "id": str(uuid.uuid4()),
                    "descricao": "Risk",
                    "severidade": "alta",
                    "componentes_afetados": ["API Gateway"],
                    "recomendacao": {
                        "descricao": "Fix it",
                        "prioridade": "alta",
                    },
                }
            ],
        }

        with (
            patch("src.interface.controllers.v1.processamento_controller.get_session") as mock_session,
            patch(
                "src.interface.controllers.v1.processamento_controller.SQLAlchemyProcessamentoRepository"
            ) as mock_repo_class,
            patch("src.interface.controllers.v1.processamento_controller.GetProcessingResult") as mock_use_case_class,
        ):
            mock_session.return_value.__aenter__.return_value = AsyncMock()
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo
            mock_use_case = AsyncMock()
            mock_use_case.execute.return_value = mock_response_dto
            mock_use_case_class.return_value = mock_use_case

            async with AsyncClient(transport=transport, base_url="http://test") as client:
                # Act
                response = await client.get(f"/api/v1/processamentos/{analise_id}")

                # Assert
                assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_processamento_not_found(self) -> None:
        """Test GET /api/v1/processamentos/{analise_id} returns 404 when not found."""
        # Arrange
        analise_id = uuid.uuid4()
        transport = ASGITransport(app=app)

        with (
            patch("src.interface.controllers.v1.processamento_controller.get_session") as mock_session,
            patch(
                "src.interface.controllers.v1.processamento_controller.SQLAlchemyProcessamentoRepository"
            ) as mock_repo_class,
            patch("src.interface.controllers.v1.processamento_controller.GetProcessingResult") as mock_use_case_class,
        ):
            mock_session.return_value.__aenter__.return_value = AsyncMock()
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo

            from src.domain.exceptions import ProcessamentoNaoEncontradoError

            mock_use_case = AsyncMock()
            mock_use_case.execute.side_effect = ProcessamentoNaoEncontradoError("Not found")
            mock_use_case_class.return_value = mock_use_case

            async with AsyncClient(transport=transport, base_url="http://test") as client:
                # Act
                response = await client.get(f"/api/v1/processamentos/{analise_id}")

                # Assert
                assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_processamento_invalid_uuid(self) -> None:
        """Test GET endpoint with invalid UUID format."""
        # Arrange
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Act
            response = await client.get("/api/v1/processamentos/not-a-uuid")

            # Assert
            assert response.status_code == 422  # Validation error
