import abc

from src.domain.schemas import AnaliseResultSchema


class AnalysisPipeline(abc.ABC):
    """Port (interface) para o pipeline de análise de diagramas arquiteturais."""

    @abc.abstractmethod
    async def run(self, image_b64: str) -> AnaliseResultSchema:
        """
        Executa o pipeline de análise sobre a imagem do diagrama.

        Args:
            image_b64: Imagem do diagrama codificada em base64.

        Returns:
            Schema validado com componentes e riscos identificados.
        """
