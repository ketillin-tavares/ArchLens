import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests


NERDGRAPH_URL = "https://api.newrelic.com/graphql"
STATE_FILE = Path(__file__).parent / ".alerts_state.json"

POLICY_NAME = "ArchLens - Platform Alerts"


@dataclass
class AlertCondition:
    """Define uma NRQL Alert Condition."""

    name: str
    nrql: str
    warning_threshold: float
    critical_threshold: float
    threshold_duration: int  # segundos (múltiplo de 60)
    operator: str = "ABOVE"  # ABOVE ou BELOW
    fill_option: str = "STATIC"
    fill_value: float = 0
    description: str = ""


# ---------------------------------------------------------------------------
# Todas as 21 condições de alerta
# ---------------------------------------------------------------------------

CONDITIONS: list[AlertCondition] = [
    # ── 1-3: Error Rate por serviço ──────────────────────────────────────
    AlertCondition(
        name="Error Rate — upload-service",
        nrql="SELECT percentage(count(*), WHERE error IS true) FROM Transaction WHERE appName = 'upload-service'",
        warning_threshold=2,
        critical_threshold=5,
        threshold_duration=300,
        description="Taxa de erro HTTP do upload-service acima do aceitável.",
    ),
    AlertCondition(
        name="Error Rate — processing-service",
        nrql="SELECT percentage(count(*), WHERE error IS true) FROM Transaction WHERE appName = 'processing-service'",
        warning_threshold=2,
        critical_threshold=5,
        threshold_duration=300,
        description="Taxa de erro HTTP do processing-service acima do aceitável.",
    ),
    AlertCondition(
        name="Error Rate — report-service",
        nrql="SELECT percentage(count(*), WHERE error IS true) FROM Transaction WHERE appName = 'report-service'",
        warning_threshold=2,
        critical_threshold=5,
        threshold_duration=300,
        description="Taxa de erro HTTP do report-service acima do aceitável.",
    ),
    # ── 4-6: P95 Latência por serviço ────────────────────────────────────
    AlertCondition(
        name="P95 Latência — upload-service",
        nrql="SELECT percentile(duration, 95) FROM Transaction WHERE appName = 'upload-service'",
        warning_threshold=2,
        critical_threshold=10,
        threshold_duration=300,
        description="Latência P95 do upload-service degradada.",
    ),
    AlertCondition(
        name="P95 Latência — processing-service",
        nrql="SELECT percentile(duration, 95) FROM Transaction WHERE appName = 'processing-service'",
        warning_threshold=60,
        critical_threshold=120,
        threshold_duration=300,
        description="Latência P95 do processing-service (pipeline AI) degradada.",
    ),
    AlertCondition(
        name="P95 Latência — report-service",
        nrql="SELECT percentile(duration, 95) FROM Transaction WHERE appName = 'report-service'",
        warning_threshold=30,
        critical_threshold=60,
        threshold_duration=300,
        description="Latência P95 do report-service degradada.",
    ),
    # ── 7: Pipeline E2E ──────────────────────────────────────────────────
    AlertCondition(
        name="Pipeline E2E — Tempo Total",
        nrql="SELECT average(newrelic.timeslice.value) FROM Metric WHERE metricTimesliceName = 'Custom/Analise/TempoProcessamento'",
        warning_threshold=120,
        critical_threshold=300,
        threshold_duration=600,
        description="Tempo total do pipeline (upload → relatório) acima do esperado.",
    ),
    # ── 8: Falhas no Pipeline ────────────────────────────────────────────
    AlertCondition(
        name="Pipeline — Falhas",
        nrql="SELECT sum(newrelic.timeslice.value) FROM Metric WHERE metricTimesliceName = 'Custom/Analise/Falhas'",
        warning_threshold=1,
        critical_threshold=5,
        threshold_duration=300,
        description="Falhas detectadas no pipeline de análise.",
    ),
    # ── 9-11: Dead Letter Queues ─────────────────────────────────────────
    AlertCondition(
        name="DLQ — processing-service",
        nrql="SELECT average(queue.messagesReadyCount) FROM RabbitmqQueueSample WHERE queue.name = 'processing-service.pipeline.dlq'",
        warning_threshold=1,
        critical_threshold=10,
        threshold_duration=300,
        description="Mensagens acumuladas na DLQ do processing-service.",
    ),
    AlertCondition(
        name="DLQ — report-service",
        nrql="SELECT average(queue.messagesReadyCount) FROM RabbitmqQueueSample WHERE queue.name = 'report-service.reports.dlq'",
        warning_threshold=1,
        critical_threshold=10,
        threshold_duration=300,
        description="Mensagens acumuladas na DLQ do report-service.",
    ),
    AlertCondition(
        name="DLQ — upload-service",
        nrql="SELECT average(queue.messagesReadyCount) FROM RabbitmqQueueSample WHERE queue.name = 'upload-service.status-updates.dlq'",
        warning_threshold=1,
        critical_threshold=10,
        threshold_duration=300,
        description="Mensagens acumuladas na DLQ do upload-service.",
    ),
    # ── 12: Queue Depth ──────────────────────────────────────────────────
    AlertCondition(
        name="Queue Depth — processing-service.pipeline",
        nrql="SELECT average(queue.messagesReadyCount) FROM RabbitmqQueueSample WHERE queue.name = 'processing-service.pipeline'",
        warning_threshold=50,
        critical_threshold=200,
        threshold_duration=600,
        description="Backlog crescente na fila principal do processing-service.",
    ),
    # ── 13: AI Confiança ─────────────────────────────────────────────────
    AlertCondition(
        name="AI — Confiança Média Baixa",
        nrql="SELECT average(newrelic.timeslice.value) FROM Metric WHERE metricTimesliceName = 'Custom/AI/AvgConfidence'",
        warning_threshold=0.75,
        critical_threshold=0.60,
        threshold_duration=900,
        operator="BELOW",
        description="Confiança média dos componentes detectados pela IA abaixo do aceitável.",
    ),
    # ── 14: AI Validation Retries ────────────────────────────────────────
    AlertCondition(
        name="AI — Retentativas de Validação",
        nrql="SELECT sum(newrelic.timeslice.value) FROM Metric WHERE metricTimesliceName = 'Custom/AI/ValidationRetries'",
        warning_threshold=10,
        critical_threshold=30,
        threshold_duration=600,
        description="IA produzindo outputs inválidos com frequência alta.",
    ),
    # ── 15: AI AnaliseFalha ──────────────────────────────────────────────
    AlertCondition(
        name="AI — AnaliseFalha (eventos)",
        nrql="SELECT count(*) FROM AnaliseFalha",
        warning_threshold=2,
        critical_threshold=5,
        threshold_duration=300,
        description="Falhas no pipeline de IA detectadas via custom events.",
    ),
    # ── 16: CPU Container ────────────────────────────────────────────────
    AlertCondition(
        name="Infra — CPU Container",
        nrql="SELECT average(cpuPercent) FROM ContainerSample WHERE containerName IN ('upload-service', 'processing-service', 'report-service') FACET containerName",
        warning_threshold=70,
        critical_threshold=85,
        threshold_duration=300,
        description="CPU de container de serviço acima do threshold.",
    ),
    # ── 17: Memória Container ────────────────────────────────────────────
    AlertCondition(
        name="Infra — Memória Container",
        nrql="SELECT average(memoryUsageBytes) / average(memoryLimitBytes) * 100 FROM ContainerSample WHERE containerName IN ('upload-service', 'processing-service', 'report-service') FACET containerName",
        warning_threshold=75,
        critical_threshold=90,
        threshold_duration=300,
        description="Memória de container de serviço acima do threshold.",
    ),
    # ── 18: Error Logs Volume ────────────────────────────────────────────
    AlertCondition(
        name="Logs — Volume de Erros",
        nrql="SELECT count(*) FROM Log WHERE level = 'ERROR' AND service.name IN ('upload-service', 'processing-service', 'report-service') FACET service.name",
        warning_threshold=10,
        critical_threshold=50,
        threshold_duration=300,
        description="Burst de logs de erro detectado.",
    ),
    # ── 19: Apdex upload-service ─────────────────────────────────────────
    AlertCondition(
        name="Apdex — upload-service",
        nrql="SELECT apdex(duration, 0.5) FROM Transaction WHERE appName = 'upload-service'",
        warning_threshold=0.85,
        critical_threshold=0.70,
        threshold_duration=600,
        operator="BELOW",
        description="Experiência do usuário no upload-service degradada.",
    ),
    # ── 20: Tempo Geração Relatório ──────────────────────────────────────
    AlertCondition(
        name="Report — Tempo de Geração",
        nrql="SELECT average(newrelic.timeslice.value) FROM Metric WHERE metricTimesliceName = 'Custom/Relatorio/TempoGeracao'",
        warning_threshold=30,
        critical_threshold=60,
        threshold_duration=600,
        description="LiteLLM demorando mais que o esperado para gerar relatórios.",
    ),
    # ── 21: DB Query Latência ────────────────────────────────────────────
    AlertCondition(
        name="DB — Query Latência",
        nrql="SELECT average(databaseDuration) FROM Transaction WHERE appName IN ('upload-service', 'processing-service', 'report-service') AND databaseDuration IS NOT NULL FACET appName",
        warning_threshold=0.5,
        critical_threshold=2,
        threshold_duration=300,
        description="Queries PostgreSQL lentas impactando a aplicação.",
    ),
]


# ---------------------------------------------------------------------------
# NerdGraph helpers
# ---------------------------------------------------------------------------


def _get_config() -> tuple[str, int]:
    """
    Obtém API key e account ID das variáveis de ambiente.

    Returns:
        Tupla (api_key, account_id).

    Raises:
        SystemExit: Se as variáveis não estiverem definidas.
    """

    api_key = "change-me"
    account_id_str = "change-me"

    if not api_key:
        print("ERRO: Defina NEW_RELIC_USER_KEY no ambiente.")
        print("  export NEW_RELIC_USER_KEY='NRAK-...'")
        sys.exit(1)

    return api_key, int(account_id_str)


def _nerdgraph(
    api_key: str, query: str, variables: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Executa uma query/mutation no NerdGraph.

    Args:
        api_key: User API key do New Relic.
        query: Query ou mutation GraphQL.
        variables: Variáveis opcionais.

    Returns:
        Resposta JSON do NerdGraph.

    Raises:
        SystemExit: Se a requisição falhar.
    """
    payload: dict[str, Any] = {"query": query}
    if variables:
        payload["variables"] = variables

    resp = requests.post(
        NERDGRAPH_URL,
        headers={"API-Key": api_key, "Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )

    if resp.status_code != 200:
        print(f"ERRO HTTP {resp.status_code}: {resp.text}")
        sys.exit(1)

    data = resp.json()
    if "errors" in data and data["errors"]:
        print(f"ERRO NerdGraph: {json.dumps(data['errors'], indent=2)}")
        sys.exit(1)

    return data


# ---------------------------------------------------------------------------
# State management (para --destroy)
# ---------------------------------------------------------------------------


def _save_state(state: dict[str, Any]) -> None:
    """Salva o estado dos recursos criados para permitir destruição posterior."""
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _load_state() -> dict[str, Any]:
    """Carrega o estado salvo dos recursos criados."""
    if not STATE_FILE.exists():
        return {}
    return json.loads(STATE_FILE.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


def create_policy(api_key: str, account_id: int) -> int:
    """
    Cria a Alert Policy no New Relic.

    Args:
        api_key: User API key.
        account_id: Account ID.

    Returns:
        ID da policy criada.
    """
    mutation = """
    mutation($accountId: Int!, $name: String!) {
      alertsPolicyCreate(accountId: $accountId, policy: {
        incidentPreference: PER_CONDITION_AND_TARGET
        name: $name
      }) {
        id
        name
      }
    }
    """
    data = _nerdgraph(api_key, mutation, {"accountId": account_id, "name": POLICY_NAME})
    policy_id = int(data["data"]["alertsPolicyCreate"]["id"])
    print(f"  Policy criada: {POLICY_NAME} (ID: {policy_id})")
    return policy_id


def create_condition(
    api_key: str,
    account_id: int,
    policy_id: int,
    condition: AlertCondition,
) -> int:
    """
    Cria uma NRQL Alert Condition estática no New Relic.

    Args:
        api_key: User API key.
        account_id: Account ID.
        policy_id: ID da policy pai.
        condition: Definição da condição.

    Returns:
        ID da condição criada.
    """
    mutation = """
    mutation CreateCondition($accountId: Int!, $policyId: ID!, $condition: AlertsNrqlConditionStaticInput!) {
      alertsNrqlConditionStaticCreate(
        accountId: $accountId,
        policyId: $policyId,
        condition: $condition
      ) {
        id
        name
      }
    }
    """

    terms = [
        {
            "threshold": condition.critical_threshold,
            "thresholdOccurrences": "ALL",
            "thresholdDuration": condition.threshold_duration,
            "operator": condition.operator,
            "priority": "CRITICAL",
        },
        {
            "threshold": condition.warning_threshold,
            "thresholdOccurrences": "ALL",
            "thresholdDuration": condition.threshold_duration,
            "operator": condition.operator,
            "priority": "WARNING",
        },
    ]

    condition_input: dict[str, Any] = {
        "name": condition.name,
        "description": condition.description,
        "enabled": True,
        "nrql": {"query": condition.nrql},
        "signal": {
            "aggregationWindow": 60,
            "aggregationMethod": "EVENT_FLOW",
            "aggregationDelay": 120,
            "fillOption": condition.fill_option,
            "fillValue": condition.fill_value,
        },
        "terms": terms,
        "violationTimeLimitSeconds": 86400,
    }

    data = _nerdgraph(
        api_key,
        mutation,
        {
            "accountId": account_id,
            "policyId": str(policy_id),
            "condition": condition_input,
        },
    )

    condition_id = int(data["data"]["alertsNrqlConditionStaticCreate"]["id"])
    return condition_id


# ---------------------------------------------------------------------------
# Destroy
# ---------------------------------------------------------------------------


def destroy_condition(api_key: str, account_id: int, condition_id: int) -> None:
    """
    Remove uma NRQL Alert Condition.

    Args:
        api_key: User API key.
        account_id: Account ID.
        condition_id: ID da condição a remover.
    """
    mutation = """
    mutation($accountId: Int!, $id: ID!) {
      alertsConditionDelete(accountId: $accountId, id: $id) {
        id
      }
    }
    """
    _nerdgraph(api_key, mutation, {"accountId": account_id, "id": str(condition_id)})


def destroy_policy(api_key: str, account_id: int, policy_id: int) -> None:
    """
    Remove uma Alert Policy.

    Args:
        api_key: User API key.
        account_id: Account ID.
        policy_id: ID da policy a remover.
    """
    mutation = """
    mutation($accountId: Int!, $id: ID!) {
      alertsPolicyDelete(accountId: $accountId, id: $id) {
        id
      }
    }
    """
    _nerdgraph(api_key, mutation, {"accountId": account_id, "id": str(policy_id)})


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def run_create() -> None:
    """Cria a policy e todas as 21 condições de alerta."""
    api_key, account_id = _get_config()

    print(f"\n{'=' * 60}")
    print("  ArchLens — Provisionamento de Alertas (New Relic)")
    print(f"  Account: {account_id}")
    print(f"  Condições: {len(CONDITIONS)}")
    print(f"{'=' * 60}\n")

    print("[1/2] Criando Alert Policy...")
    policy_id = create_policy(api_key, account_id)

    print(f"\n[2/2] Criando {len(CONDITIONS)} condições de alerta...\n")

    created_conditions: list[dict[str, Any]] = []

    for i, cond in enumerate(CONDITIONS, 1):
        condition_id = create_condition(api_key, account_id, policy_id, cond)
        created_conditions.append({"id": condition_id, "name": cond.name})
        op_symbol = ">" if cond.operator == "ABOVE" else "<"
        print(
            f"  [{i:2d}/{len(CONDITIONS)}] {cond.name}"
            f"  (warn {op_symbol} {cond.warning_threshold}, "
            f"crit {op_symbol} {cond.critical_threshold}, "
            f"janela {cond.threshold_duration}s)"
        )

    state = {
        "account_id": account_id,
        "policy_id": policy_id,
        "policy_name": POLICY_NAME,
        "conditions": created_conditions,
    }
    _save_state(state)

    print(f"\n{'=' * 60}")
    print(f"  SUCESSO! {len(CONDITIONS)} alertas criados.")
    print(f"  Policy ID: {policy_id}")
    print(f"  Estado salvo em: {STATE_FILE}")
    print(f"  Para destruir: python {Path(__file__).name} --destroy")
    print(f"{'=' * 60}\n")


def run_destroy() -> None:
    """Remove todos os recursos criados (policy + condições)."""
    api_key, account_id = _get_config()
    state = _load_state()

    if not state:
        print("Nenhum estado encontrado. Nada para destruir.")
        sys.exit(0)

    print(f"\n{'=' * 60}")
    print("  ArchLens — Destruição de Alertas")
    print(f"  Policy: {state.get('policy_name')} (ID: {state.get('policy_id')})")
    print(f"  Condições: {len(state.get('conditions', []))}")
    print(f"{'=' * 60}\n")

    conditions = state.get("conditions", [])
    for i, cond in enumerate(conditions, 1):
        print(
            f"  [{i:2d}/{len(conditions)}] Removendo: {cond['name']} (ID: {cond['id']})"
        )
        destroy_condition(api_key, account_id, cond["id"])

    print(f"\n  Removendo policy ID {state['policy_id']}...")
    destroy_policy(api_key, account_id, state["policy_id"])

    STATE_FILE.unlink(missing_ok=True)

    print("\n  SUCESSO! Todos os alertas foram removidos.\n")


def main() -> None:
    """Entry point do script."""
    parser = argparse.ArgumentParser(
        description="ArchLens — Provisionamento de alertas no New Relic via NerdGraph.",
    )
    parser.add_argument(
        "--destroy",
        action="store_true",
        help="Remove todos os alertas criados anteriormente.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Apenas lista as condições que seriam criadas, sem executar.",
    )

    args = parser.parse_args()

    if args.dry_run:
        print(f"\n  DRY RUN — {len(CONDITIONS)} condições configuradas:\n")
        for i, cond in enumerate(CONDITIONS, 1):
            op_symbol = ">" if cond.operator == "ABOVE" else "<"
            print(f"  [{i:2d}] {cond.name}")
            print(f"       NRQL: {cond.nrql}")
            print(
                f"       Warning {op_symbol} {cond.warning_threshold} | "
                f"Critical {op_symbol} {cond.critical_threshold} | "
                f"Janela: {cond.threshold_duration}s"
            )
            print(f"       Fill: {cond.fill_option} ({cond.fill_value})")
            print()
        return

    if args.destroy:
        run_destroy()
    else:
        run_create()


if __name__ == "__main__":
    main()

# Como usar

# # 1. Definir a API key e Account ID

# # 2. Ver o que será criado (sem executar)
# python docs/newrelic/setup_alerts.py --dry-run

# # 3. Criar tudo (policy + 21 condições)
# python docs/newrelic/setup_alerts.py

# # 4. Se precisar remover tudo
# python docs/newrelic/setup_alerts.py --destroy
