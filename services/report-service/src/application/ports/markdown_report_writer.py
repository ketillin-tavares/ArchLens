import abc
from typing import Any


class MarkdownReportWriter(abc.ABC):
    """Port (interface) para geração de relatório Markdown via agente de IA."""

    @abc.abstractmethod
    async def generate(
        self,
        titulo: str,
        resumo: str,
        componentes: list[dict[str, Any]],
        riscos: list[dict[str, Any]],
        estatisticas: dict[str, Any],
    ) -> str:
        """
        Gera um relatório narrativo em Markdown a partir dos dados estruturados.

        Args:
            titulo: Título do relatório.
            resumo: Resumo descritivo gerado pelas estatísticas.
            componentes: Lista de componentes arquiteturais identificados.
            riscos: Lista de riscos identificados com severidade e recomendações.
            estatisticas: Estatísticas agregadas (totais, distribuição por severidade).

        Returns:
            String contendo o relatório completo em Markdown.
        """
