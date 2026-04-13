"""
Golden Set — Testes de regressão de prompt do pipeline de análise de IA.

Cada test case representa um diagrama de referência com saída esperada conhecida.
Esses testes chamam o LLM real e devem ser executados isoladamente do CI unitário:

    pytest -m integration

Referência de resultado esperado: relatorio.md (Netflix Backend in AWS)
Diagrama de referência:           tests/fixtures/diagrama_netflix_backend_aws.png
"""

import base64
from pathlib import Path
from typing import Any

import pytest

from src.application.sanity_checks import check_sanity
from src.domain.schemas import AnaliseResultSchema, Severidade, TipoComponente
from src.infrastructure.agents.single_call_pipeline import SingleCallPipeline

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"

# ---------------------------------------------------------------------------
# Golden Set — definição dos casos de teste
# ---------------------------------------------------------------------------
# Cada entrada deve conter ao menos uma das chaves de asserção abaixo:
#   expected_components         — lista de nomes que DEVEM estar presentes
#   expected_components_min     — número mínimo de componentes
#   expected_components_max     — número máximo de componentes
#   expected_types_include      — lista de TipoComponente que devem aparecer
#   expected_min_risks          — número mínimo de riscos
#   expected_severities_include — lista de Severidade que devem aparecer pelo menos uma vez
#
# Fonte: relatorio.md — análise gerada sobre diagrama_netflix_backend_aws.png
# Componentes detectados (10): CLIENT DEVICES, AWS ELB, API GATEWAY SERVICE,
#   APPLICATION API, CACHE, MICRO SERVICE, DATASTORES, STREAM PROCESSING PIPELINE,
#   AWS S3, HADOOP
# Riscos detectados (4): Acoplamento BD, SPOF entrada, Falta resiliência,
#   Ausência observabilidade

GOLDEN_TESTS: list[dict[str, Any]] = [
    {
        "id": "netflix_backend_aws",
        "image": FIXTURES_DIR / "diagrama_netflix_backend_aws.png",
        "description": (
            "Netflix Backend in AWS — microsserviços com ELB, API Gateway, "
            "Application API, Cache, MicroService, Datastores, Stream Processing, S3, Hadoop"
        ),
        # Componentes com labels explícitas e inequívocas no diagrama
        "expected_components": [
            "AWS ELB",
            "API GATEWAY SERVICE",
            "MICRO SERVICE",
            "DATASTORES",
            "CACHE",
            "AWS S3",
            "HADOOP",
        ],
        # Cardinalidade: o diagrama tem 10 componentes claramente rotulados;
        # toleramos entre 7 e 12 para cobrir variações de granularidade da IA
        # (ex: APPLICATION API pode ser detectada como um bloco ou como 3 sub-APIs)
        "expected_components_min": 7,
        "expected_components_max": 12,
        # Tipos mínimos que devem aparecer, independente de como os nomes são escritos
        "expected_types_include": [
            TipoComponente.LOAD_BALANCER,
            TipoComponente.API_GATEWAY,
            TipoComponente.SERVICE,
            TipoComponente.DATABASE,
            TipoComponente.CACHE,
            TipoComponente.STORAGE,
        ],
        # O diagrama tem 4 riscos identificados no relatorio.md; aceitamos >= 2
        "expected_min_risks": 2,
        # Devem existir ao menos um risco de severidade alta ou crítica
        # (Acoplamento de BD e SPOF são os mais evidentes)
        "expected_severities_include": [Severidade.ALTA, Severidade.CRITICA],
    },
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_image_as_b64(image_path: Path) -> str:
    """
    Lê uma imagem do disco e a codifica em base64.

    Args:
        image_path: Caminho absoluto para a imagem.

    Returns:
        String base64 da imagem.

    Raises:
        FileNotFoundError: Se a imagem não existir no caminho informado.
    """
    if not image_path.exists():
        raise FileNotFoundError(
            f"Fixture de imagem não encontrada: {image_path}. Verifique se o arquivo está em tests/fixtures/."
        )
    return base64.b64encode(image_path.read_bytes()).decode("utf-8")


def _assert_components(result: AnaliseResultSchema, test_case: dict[str, Any]) -> None:
    """
    Verifica as asserções sobre componentes detectados.

    Args:
        result:    Resultado da análise.
        test_case: Dicionário com as expectativas do golden test.
    """
    detected_names = {c.nome for c in result.componentes}
    detected_types = {c.tipo for c in result.componentes}

    if "expected_components" in test_case:
        for expected_name in test_case["expected_components"]:
            assert expected_name in detected_names, (
                f"Componente '{expected_name}' não detectado. Detectados: {sorted(detected_names)}"
            )

    if "expected_components_min" in test_case:
        assert len(result.componentes) >= test_case["expected_components_min"], (
            f"Esperado ao menos {test_case['expected_components_min']} componentes, "
            f"detectados {len(result.componentes)}: {sorted(detected_names)}"
        )

    if "expected_components_max" in test_case:
        assert len(result.componentes) <= test_case["expected_components_max"], (
            f"Esperado no máximo {test_case['expected_components_max']} componentes, "
            f"detectados {len(result.componentes)}: {sorted(detected_names)}. "
            "Possível alucinação — verifique o prompt."
        )

    if "expected_types_include" in test_case:
        for expected_type in test_case["expected_types_include"]:
            assert expected_type in detected_types, (
                f"Tipo de componente '{expected_type}' não encontrado nos resultados. "
                f"Tipos detectados: {sorted(t.value for t in detected_types)}"
            )


def _assert_risks(result: AnaliseResultSchema, test_case: dict[str, Any]) -> None:
    """
    Verifica as asserções sobre riscos identificados.

    Args:
        result:    Resultado da análise.
        test_case: Dicionário com as expectativas do golden test.
    """
    if "expected_min_risks" in test_case:
        assert len(result.riscos) >= test_case["expected_min_risks"], (
            f"Esperado ao menos {test_case['expected_min_risks']} riscos, identificados {len(result.riscos)}."
        )

    if "expected_severities_include" in test_case:
        detected_severities = {r.severidade for r in result.riscos}
        expected_severities: list[Severidade] = test_case["expected_severities_include"]
        has_expected = any(s in detected_severities for s in expected_severities)
        assert has_expected, (
            f"Nenhuma das severidades esperadas {[s.value for s in expected_severities]} "
            f"foi encontrada. Severidades detectadas: {[s.value for s in detected_severities]}"
        )


def _assert_schema_compliance(result: AnaliseResultSchema) -> None:
    """
    Verifica invariantes de schema que devem valer para qualquer resultado válido.

    Args:
        result: Resultado da análise já validado pelo Pydantic.
    """
    for componente in result.componentes:
        assert 0.0 <= componente.confianca <= 1.0, (
            f"Confiança fora do intervalo [0,1] para '{componente.nome}': {componente.confianca}"
        )
        assert componente.tipo is not None, f"Componente '{componente.nome}' sem tipo definido."
        assert componente.metadata.descricao, f"Componente '{componente.nome}' com descrição vazia."

    nomes_componentes = {c.nome for c in result.componentes}
    for risco in result.riscos:
        for afetado in risco.componentes_afetados:
            assert afetado in nomes_componentes, (
                f"Risco '{risco.descricao}' referencia componente inexistente: '{afetado}'. "
                f"Componentes válidos: {sorted(nomes_componentes)}"
            )


# ---------------------------------------------------------------------------
# Golden Set Tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.parametrize("test_case", GOLDEN_TESTS, ids=[tc["id"] for tc in GOLDEN_TESTS])
@pytest.mark.asyncio
async def test_golden_set(test_case: dict[str, Any], ai_pipeline: SingleCallPipeline) -> None:
    """
    Verifica se o pipeline de IA extrai os componentes e riscos esperados
    dos diagramas de referência do golden set.

    Falha neste teste indica que uma mudança de prompt ou de modelo degradou
    a qualidade de extração — deve ser investigada antes do merge.

    Args:
        test_case:   Dicionário com a definição do caso de teste (imagem + expectativas).
        ai_pipeline: Pipeline real instanciado com LLM client (fixture de integration/conftest.py).
    """
    # Arrange
    image_b64 = _load_image_as_b64(test_case["image"])

    # Act
    result = await ai_pipeline.run(image_b64)

    # Assert — schema compliance (invariantes Pydantic)
    _assert_schema_compliance(result)

    # Assert — sanity checks (guardrails de alucinação)
    check_sanity(result)

    # Assert — componentes esperados
    _assert_components(result, test_case)

    # Assert — riscos esperados
    _assert_risks(result, test_case)
