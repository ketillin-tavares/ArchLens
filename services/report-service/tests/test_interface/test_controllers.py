"""Integration tests for API controllers."""

import uuid
from unittest.mock import AsyncMock, patch

from httpx import AsyncClient

from src.domain.entities import Relatorio
from src.main import app


class TestRelatorioController:
    """Integration tests for the Relatorio controller."""

    async def test_get_report_success(self, async_client: AsyncClient) -> None:
        """Test GET /v1/relatorios/{analise_id} returns 200 with relatório."""
        # Arrange
        analise_id = uuid.uuid4()
        relatorio_id = uuid.uuid4()

        relatorio = Relatorio(
            id=relatorio_id,
            analise_id=analise_id,
            titulo="Test Report",
            resumo="Test Summary",
            conteudo={"test": "data"},
        )

        # Mock the repository
        with patch(
            "src.interface.controllers.v1.relatorio_controller.SQLAlchemyRelatorioRepository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.buscar_por_analise_id.return_value = relatorio
            mock_repo_class.return_value = mock_repo

            # Mock the session dependency
            with patch("src.interface.controllers.v1.relatorio_controller.get_session") as mock_session:
                mock_session_obj = AsyncMock()
                mock_session.return_value = mock_session_obj

                # Override the dependency
                def get_session_override():
                    return mock_session_obj

                from src.interface.controllers.v1 import relatorio_controller

                app.dependency_overrides[relatorio_controller.get_session] = get_session_override

                # Act
                response = await async_client.get(f"/v1/relatorios/{analise_id}")

                # Assert
                assert response.status_code == 200
                data = response.json()
                assert str(relatorio_id) == data["id"]
                assert str(analise_id) == data["analise_id"]
                assert data["titulo"] == "Test Report"
                assert data["resumo"] == "Test Summary"

                # Cleanup
                app.dependency_overrides.clear()

    async def test_get_report_not_found(self, async_client: AsyncClient) -> None:
        """Test GET /v1/relatorios/{analise_id} returns 404 when not found."""
        # Arrange
        analise_id = uuid.uuid4()

        # Mock the repository to return None
        with patch(
            "src.interface.controllers.v1.relatorio_controller.SQLAlchemyRelatorioRepository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.buscar_por_analise_id.return_value = None
            mock_repo_class.return_value = mock_repo

            # Mock the session dependency
            with patch("src.interface.controllers.v1.relatorio_controller.get_session") as mock_session:
                mock_session_obj = AsyncMock()
                mock_session.return_value = mock_session_obj

                def get_session_override():
                    return mock_session_obj

                from src.interface.controllers.v1 import relatorio_controller

                app.dependency_overrides[relatorio_controller.get_session] = get_session_override

                # Act
                response = await async_client.get(f"/v1/relatorios/{analise_id}")

                # Assert
                assert response.status_code == 404
                data = response.json()
                assert "detail" in data

                # Cleanup
                app.dependency_overrides.clear()

    async def test_get_report_invalid_uuid(self, async_client: AsyncClient) -> None:
        """Test GET with invalid UUID format returns 422."""
        # Act
        response = await async_client.get("/v1/relatorios/invalid-uuid")

        # Assert
        assert response.status_code == 422

    async def test_get_report_with_complex_conteudo(self, async_client: AsyncClient) -> None:
        """Test GET returns relatório with complex conteudo structure."""
        # Arrange
        analise_id = uuid.uuid4()
        relatorio_id = uuid.uuid4()

        conteudo = {
            "componentes": [
                {"id": "1", "nome": "API", "dependencies": ["DB"]},
                {"id": "2", "nome": "DB", "dependencies": []},
            ],
            "riscos": [
                {"id": "1", "severidade": "alta", "impacto": 0.8},
            ],
            "estatisticas": {
                "total_componentes": 2,
                "total_riscos": 1,
                "riscos_por_severidade": {"critica": 0, "alta": 1, "media": 0, "baixa": 0},
            },
        }

        relatorio = Relatorio(
            id=relatorio_id,
            analise_id=analise_id,
            titulo="Complex Report",
            resumo="Complex Summary",
            conteudo=conteudo,
        )

        with patch(
            "src.interface.controllers.v1.relatorio_controller.SQLAlchemyRelatorioRepository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.buscar_por_analise_id.return_value = relatorio
            mock_repo_class.return_value = mock_repo

            with patch("src.interface.controllers.v1.relatorio_controller.get_session") as mock_session:
                mock_session_obj = AsyncMock()
                mock_session.return_value = mock_session_obj

                def get_session_override():
                    return mock_session_obj

                from src.interface.controllers.v1 import relatorio_controller

                app.dependency_overrides[relatorio_controller.get_session] = get_session_override

                # Act
                response = await async_client.get(f"/v1/relatorios/{analise_id}")

                # Assert
                assert response.status_code == 200
                data = response.json()
                assert len(data["conteudo"]["componentes"]) == 2
                assert len(data["conteudo"]["riscos"]) == 1
                assert data["conteudo"]["estatisticas"]["total_componentes"] == 2

                app.dependency_overrides.clear()
