from pydantic import BaseModel, Field


class MarkdownReportOutput(BaseModel):
    """Schema de saída do Report Writer Agent."""

    markdown: str = Field(
        ...,
        min_length=100,
        description="Relatório completo em Markdown, pronto para ser salvo como arquivo .md",
    )
