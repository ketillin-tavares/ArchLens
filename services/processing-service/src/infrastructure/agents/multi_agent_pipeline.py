from pydantic_ai.models.openai import OpenAIChatModel

from src.application.sanity_checks import check_sanity
from src.domain.exceptions import AnaliseInsanaError
from src.domain.schemas import AnaliseResultSchema
from src.infrastructure.agents.analyzer_agent import AnalyzerAgent
from src.infrastructure.agents.extractor_agent import ExtractorAgent
from src.infrastructure.agents.judge_agent import JudgeAgent
from src.infrastructure.observability.logging import get_logger

logger = get_logger()

JUDGE_THRESHOLD: float = 7.0


class MultiAgentPipeline:
    """Pipeline multi-agent: Extractor → Analyzer → Judge (opcional)."""

    def __init__(
        self,
        vision_model: OpenAIChatModel,
        analyzer_model: OpenAIChatModel,
        enable_judge: bool = False,
    ) -> None:
        self._extractor = ExtractorAgent(model=vision_model)
        self._analyzer = AnalyzerAgent(model=analyzer_model)
        self._judge = JudgeAgent(model=vision_model) if enable_judge else None

    async def run(self, image_b64: str) -> AnaliseResultSchema:
        """
        Executa o pipeline multi-agent completo.

        Etapas:
            1. Extractor: extrai componentes do diagrama (vision).
            2. Analyzer: identifica riscos a partir dos componentes (text-only).
            3. Judge (opcional): valida qualidade comparando com a imagem.

        Args:
            image_b64: Imagem do diagrama codificada em base64.

        Returns:
            Schema validado com componentes e riscos.

        Raises:
            AnaliseInsanaError: Se o Judge reprovar a análise.
        """
        logger.info("multi_agent_etapa", etapa="extractor")
        extraction = await self._extractor.run(image_b64)

        logger.info("multi_agent_etapa", etapa="analyzer")
        analysis = await self._analyzer.run(
            componentes=extraction.componentes,
            descricao_geral=extraction.descricao_geral,
        )

        result = AnaliseResultSchema(
            componentes=extraction.componentes,
            riscos=analysis.riscos,
        )

        check_sanity(result)

        if self._judge is not None:
            logger.info("multi_agent_etapa", etapa="judge")
            judgement = await self._judge.run(
                analise_result=result,
                image_b64=image_b64,
            )

            if not judgement.aprovado:
                logger.warning(
                    "judge_reprovou",
                    score_medio=judgement.score_medio,
                    comentario=judgement.comentario,
                )
                raise AnaliseInsanaError(
                    f"Judge reprovou a análise (score: {judgement.score_medio:.1f}): {judgement.comentario}"
                )

            logger.info("judge_aprovou", score_medio=judgement.score_medio)

        logger.info(
            "multi_agent_concluido",
            total_componentes=len(result.componentes),
            total_riscos=len(result.riscos),
        )
        return result
