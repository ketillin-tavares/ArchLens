import json
from typing import Any

import structlog
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from src.domain.prompts import REPORT_WRITER_SYSTEM_PROMPT, REPORT_WRITER_USER_PROMPT_TEMPLATE
from src.environment import get_settings
from src.infrastructure.agents.schemas import MarkdownReportOutput

logger = structlog.get_logger()


class ReportWriterAgent:
    """Agente LLM responsável por gerar relatórios narrativos em Markdown (text-only)."""

    def __init__(self) -> None:
        settings = get_settings()
        provider = OpenAIProvider(
            base_url=settings.llm.base_url,
            api_key=settings.llm.api_key,
        )
        model = OpenAIChatModel(
            model_name=settings.llm.model_name,
            provider=provider,
        )
        self._agent: Agent[None, MarkdownReportOutput] = Agent(  # type: ignore[assignment]
            model=model,
            system_prompt=REPORT_WRITER_SYSTEM_PROMPT,
            output_type=MarkdownReportOutput,
        )

    async def run(
        self,
        titulo: str,
        resumo: str,
        componentes: list[dict[str, Any]],
        riscos: list[dict[str, Any]],
        estatisticas: dict[str, Any],
    ) -> MarkdownReportOutput:
        """
        Executa o agente LLM para gerar o relatório Markdown.

        Args:
            titulo: Título do relatório com data.
            resumo: Resumo textual gerado pelas estatísticas.
            componentes: Lista de componentes arquiteturais identificados.
            riscos: Lista de riscos com severidade e recomendações.
            estatisticas: Estatísticas agregadas do relatório.

        Returns:
            MarkdownReportOutput com o campo markdown preenchido.
        """
        user_prompt = REPORT_WRITER_USER_PROMPT_TEMPLATE.format(
            titulo=titulo,
            resumo=resumo,
            componentes_json=json.dumps(componentes, ensure_ascii=False, indent=2),
            riscos_json=json.dumps(riscos, ensure_ascii=False, indent=2),
            estatisticas_json=json.dumps(estatisticas, ensure_ascii=False, indent=2),
        )

        result = await self._agent.run(user_prompt)
        output = result.output

        logger.info(
            "markdown_agent_ok",
            titulo=titulo,
            markdown_length=len(output.markdown),
        )

        return output
