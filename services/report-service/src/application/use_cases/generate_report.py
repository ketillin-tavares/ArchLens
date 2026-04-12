import uuid
from datetime import UTC, datetime
from typing import Any

from src.application.ports import EventPublisher, FileStorage, MarkdownReportWriter
from src.domain.entities import Relatorio
from src.domain.events import RelatorioGerado
from src.domain.repositories import RelatorioRepository
from src.infrastructure.observability.logging import get_logger

logger = get_logger()

SEVERIDADES: list[str] = ["critica", "alta", "media", "baixa"]


class GenerateReport:
    """Caso de uso para geração de relatório a partir de uma análise concluída."""

    def __init__(
        self,
        relatorio_repository: RelatorioRepository,
        event_publisher: EventPublisher,
        markdown_report_writer: MarkdownReportWriter,
        file_storage: FileStorage,
    ) -> None:
        self._relatorio_repo = relatorio_repository
        self._event_publisher = event_publisher
        self._markdown_writer = markdown_report_writer
        self._file_storage = file_storage

    async def execute(self, analise_id: str, componentes: list[dict[str, Any]], riscos: list[dict[str, Any]]) -> bool:
        """
        Gera um relatório a partir dos dados de análise concluída.

        Verifica idempotência, calcula estatísticas, monta o conteúdo JSON,
        chama o agente de IA para Markdown, faz upload no S3, persiste e
        publica RelatorioGerado. Falhas no agente ou S3 são tratadas com
        fallback gracioso (s3_key fica None, fluxo principal não é interrompido).

        Args:
            analise_id: ID da análise (string UUID).
            componentes: Lista de componentes identificados.
            riscos: Lista de riscos identificados.

        Returns:
            True se o relatório foi gerado. False se era duplicado e foi ignorado.
        """
        analise_uuid = uuid.UUID(analise_id)

        if await self._relatorio_repo.existe_por_analise_id(analise_uuid):
            logger.info("relatorio_duplicado_ignorado", analise_id=analise_id)
            return False

        estatisticas = self._calcular_estatisticas(componentes, riscos)
        titulo = self._gerar_titulo()
        resumo = self._gerar_resumo(estatisticas)

        conteudo: dict[str, Any] = {
            "componentes": componentes,
            "riscos": riscos,
            "estatisticas": estatisticas,
        }

        s3_key: str | None = None

        logger.info("markdown_agent_iniciado", analise_id=analise_id)
        markdown_content = await self._gerar_markdown(
            analise_id=analise_id,
            titulo=titulo,
            resumo=resumo,
            componentes=componentes,
            riscos=riscos,
            estatisticas=estatisticas,
        )

        if markdown_content is not None:
            s3_key = await self._armazenar_markdown(
                analise_id=analise_id,
                analise_uuid=analise_uuid,
                markdown_content=markdown_content,
            )

        relatorio = Relatorio(
            analise_id=analise_uuid,
            titulo=titulo,
            resumo=resumo,
            conteudo=conteudo,
            s3_key=s3_key,
        )

        relatorio = await self._relatorio_repo.salvar(relatorio)

        logger.info(
            "relatorio_gerado",
            analise_id=analise_id,
            relatorio_id=str(relatorio.id),
            s3_key=s3_key,
        )

        evento = RelatorioGerado(
            analise_id=analise_uuid,
            relatorio_id=relatorio.id,
            s3_key=s3_key,
        )
        await self._event_publisher.publish_event(
            event_type=evento.event_type,
            routing_key="analise.relatorio.gerado",
            payload=evento.to_message(),
        )

        return True

    async def _gerar_markdown(
        self,
        analise_id: str,
        titulo: str,
        resumo: str,
        componentes: list[dict[str, Any]],
        riscos: list[dict[str, Any]],
        estatisticas: dict[str, Any],
    ) -> str | None:
        """
        Chama o agente de IA para gerar o relatório em Markdown.

        Retorna o conteúdo Markdown em caso de sucesso, ou None em caso de falha.

        Args:
            analise_id: ID da análise (para logging).
            titulo: Título do relatório.
            resumo: Resumo textual.
            componentes: Lista de componentes.
            riscos: Lista de riscos.
            estatisticas: Estatísticas agregadas.

        Returns:
            String com o Markdown gerado, ou None se o agente falhou.
        """
        try:
            return await self._markdown_writer.generate(
                titulo=titulo,
                resumo=resumo,
                componentes=componentes,
                riscos=riscos,
                estatisticas=estatisticas,
            )
        except Exception as exc:
            logger.error("markdown_agent_falhou", analise_id=analise_id, error=str(exc))
            return None

    async def _armazenar_markdown(
        self,
        analise_id: str,
        analise_uuid: uuid.UUID,
        markdown_content: str,
    ) -> str | None:
        """
        Faz upload do Markdown no S3 e retorna a s3_key.

        Retorna a s3_key em caso de sucesso, ou None em caso de falha.

        Args:
            analise_id: ID da análise (para logging).
            analise_uuid: UUID da análise (para construir a s3_key).
            markdown_content: Conteúdo Markdown a ser armazenado.

        Returns:
            s3_key do arquivo armazenado, ou None se o upload falhou.
        """
        s3_key = f"relatorios/{analise_uuid}.md"
        try:
            await self._file_storage.upload_text(
                s3_key=s3_key,
                content=markdown_content,
                content_type="text/markdown; charset=utf-8",
            )
            logger.info("markdown_s3_upload_ok", analise_id=analise_id, s3_key=s3_key)
            return s3_key
        except Exception as exc:
            logger.error("markdown_s3_upload_falhou", analise_id=analise_id, error=str(exc))
            return None

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
