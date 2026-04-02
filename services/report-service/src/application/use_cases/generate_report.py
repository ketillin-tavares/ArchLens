from datetime import UTC, datetime
from typing import Any

import structlog

from src.application.ports import EventPublisher
from src.domain.entities import Relatorio
from src.domain.events import RelatorioGerado
from src.domain.repositories import RelatorioRepository

logger = structlog.get_logger()

SEVERIDADES: list[str] = ["critica", "alta", "media", "baixa"]


class GenerateReport:
    """Caso de uso para geração de relatório a partir de uma análise concluída."""

    def __init__(
        self,
        relatorio_repository: RelatorioRepository,
        event_publisher: EventPublisher,
    ) -> None:
        self._relatorio_repo = relatorio_repository
        self._event_publisher = event_publisher

    async def execute(self, analise_id: str, componentes: list[dict[str, Any]], riscos: list[dict[str, Any]]) -> None:
        """
        Gera um relatório a partir dos dados de análise concluída.

        Verifica idempotência, calcula estatísticas, monta o relatório,
        persiste no banco e publica o evento RelatorioGerado.

        Args:
            analise_id: ID da análise (string UUID).
            componentes: Lista de componentes identificados.
            riscos: Lista de riscos identificados.
        """
        import uuid

        analise_uuid = uuid.UUID(analise_id)

        if await self._relatorio_repo.existe_por_analise_id(analise_uuid):
            logger.info("relatorio_duplicado_ignorado", analise_id=analise_id)
            return

        estatisticas = self._calcular_estatisticas(componentes, riscos)
        titulo = self._gerar_titulo()
        resumo = self._gerar_resumo(estatisticas)

        conteudo: dict[str, Any] = {
            "componentes": componentes,
            "riscos": riscos,
            "estatisticas": estatisticas,
        }

        relatorio = Relatorio(
            analise_id=analise_uuid,
            titulo=titulo,
            resumo=resumo,
            conteudo=conteudo,
        )

        relatorio = await self._relatorio_repo.salvar(relatorio)

        logger.info(
            "relatorio_gerado",
            analise_id=analise_id,
            relatorio_id=str(relatorio.id),
        )

        evento = RelatorioGerado(
            analise_id=analise_uuid,
            relatorio_id=relatorio.id,
        )
        await self._event_publisher.publish_event(
            event_type=evento.event_type,
            routing_key="analise.relatorio.gerado",
            payload=evento.to_message(),
        )

    @staticmethod
    def _calcular_estatisticas(componentes: list[dict[str, Any]], riscos: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Calcula estatísticas agregadas dos componentes e riscos.

        Args:
            componentes: Lista de componentes identificados.
            riscos: Lista de riscos identificados.

        Returns:
            Dicionário com estatísticas calculadas.
        """
        riscos_por_severidade: dict[str, int] = {sev: 0 for sev in SEVERIDADES}
        for risco in riscos:
            severidade = risco.get("severidade", "").lower()
            if severidade in riscos_por_severidade:
                riscos_por_severidade[severidade] += 1

        return {
            "total_componentes": len(componentes),
            "total_riscos": len(riscos),
            "riscos_por_severidade": riscos_por_severidade,
        }

    @staticmethod
    def _gerar_titulo() -> str:
        """
        Gera o título do relatório com a data atual.

        Returns:
            Título formatado.
        """
        data_atual = datetime.now(UTC).strftime("%Y-%m-%d")
        return f"Análise Arquitetural - {data_atual}"

    @staticmethod
    def _gerar_resumo(estatisticas: dict[str, Any]) -> str:
        """
        Gera o resumo descritivo do relatório a partir das estatísticas.

        Args:
            estatisticas: Estatísticas calculadas.

        Returns:
            Texto descritivo do resumo.
        """
        total_comp = estatisticas["total_componentes"]
        total_riscos = estatisticas["total_riscos"]
        sev = estatisticas["riscos_por_severidade"]

        critico = sev.get("critica", 0)
        alto = sev.get("alta", 0)
        medio = sev.get("media", 0)
        baixo = sev.get("baixa", 0)

        partes_severidade: list[str] = []
        if critico:
            partes_severidade.append(f"{critico} crítico(s)")
        if alto:
            partes_severidade.append(f"{alto} alto(s)")
        if medio:
            partes_severidade.append(f"{medio} médio(s)")
        if baixo:
            partes_severidade.append(f"{baixo} baixo(s)")

        detalhes = f" ({', '.join(partes_severidade)})" if partes_severidade else ""

        return f"Foram identificados {total_comp} componentes arquiteturais e {total_riscos} riscos{detalhes}."
