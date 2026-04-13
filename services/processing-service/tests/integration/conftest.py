"""Fixtures compartilhadas para os testes de integração do pipeline de IA."""

import os

import pytest

from src.infrastructure.agents.single_call_pipeline import SingleCallPipeline
from src.infrastructure.llm.llm_client import PydanticAILLMClient


def _llm_is_configured() -> bool:
    """Verifica se as variáveis de ambiente mínimas para o LLM estão configuradas."""
    api_key = os.getenv("LLM_API_KEY", "sk-litellm")
    base_url = os.getenv("LLM_BASE_URL", "http://localhost:4000")
    return api_key != "sk-litellm" or base_url != "http://localhost:4000"


@pytest.fixture
def ai_pipeline() -> SingleCallPipeline:
    """
    Fixture que instancia o pipeline real de análise com o LLM client.

    Pula o teste se o ambiente não estiver configurado com credenciais reais
    (LLM_API_KEY diferente do padrão ou LLM_BASE_URL apontando para serviço ativo).

    Returns:
        SingleCallPipeline instanciado com PydanticAILLMClient real.
    """
    if not _llm_is_configured():
        pytest.skip(
            "Variáveis de ambiente do LLM não configuradas. "
            "Defina LLM_BASE_URL e LLM_API_KEY para rodar testes de integração."
        )

    llm_client = PydanticAILLMClient()
    return SingleCallPipeline(llm_client=llm_client)
