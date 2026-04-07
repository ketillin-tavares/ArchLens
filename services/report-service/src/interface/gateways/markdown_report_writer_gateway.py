from typing import Any

from src.application.ports import MarkdownReportWriter
from src.infrastructure.agents.report_writer_agent import ReportWriterAgent


class ReportWriterGateway(MarkdownReportWriter):
    """Adapter que implementa MarkdownReportWriter usando o ReportWriterAgent (pydantic-ai)."""

    def __init__(self, agent: ReportWriterAgent | None = None) -> None:
        self._agent = agent or ReportWriterAgent()

    async def generate(
        self,
        titulo: str,
        resumo: str,
        componentes: list[dict[str, Any]],
        riscos: list[dict[str, Any]],
        estatisticas: dict[str, Any],
    ) -> str:
        """
        Delega a geração do relatório Markdown ao ReportWriterAgent.

        Args:
            titulo: Título do relatório.
            resumo: Resumo textual das estatísticas.
            componentes: Lista de componentes arquiteturais.
            riscos: Lista de riscos identificados.
            estatisticas: Estatísticas agregadas.

        Returns:
            String com o relatório completo em Markdown.
        """
        result = await self._agent.run(
            titulo=titulo,
            resumo=resumo,
            componentes=componentes,
            riscos=riscos,
            estatisticas=estatisticas,
        )
        return result.markdown
