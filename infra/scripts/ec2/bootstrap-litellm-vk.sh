#!/bin/bash
# ══════════════════════════════════════════════════════════════════════
#  bootstrap-litellm-vk.sh — Gera Virtual Keys do LiteLLM e atualiza os
#  secrets archlens/<env>/processing e archlens/<env>/report.
#
#  Equivalente ao job k8s litellm-vk-bootstrap.yaml. Roda como script no
#  host EC2, usando AWS Secrets Manager em vez do Vault.
#
#  Idempotente: cada execucao gera 2 VKs novas (com timestamp no alias).
#  Use apenas no bootstrap inicial ou quando precisar rotacionar VKs.
#
#  Pre-requisitos:
#    - LiteLLM healthy em http://localhost:4000 (via docker compose)
#    - Secret archlens/<env>/litellm com MASTER_KEY preenchida
#    - IAM role da EC2 com permissao secretsmanager:PutSecretValue
# ══════════════════════════════════════════════════════════════════════
set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

# shellcheck source=/dev/null
source "$REPO_ROOT/.bootstrap.env"

: "${AWS_REGION:?AWS_REGION nao definido}"
: "${ENVIRONMENT:?ENVIRONMENT nao definido}"

readonly LITELLM_URL="http://localhost:4000"
readonly LITELLM_SECRET="archlens/${ENVIRONMENT}/litellm"
readonly PROCESSING_SECRET="archlens/${ENVIRONMENT}/processing"
readonly REPORT_SECRET="archlens/${ENVIRONMENT}/report"
readonly TIMESTAMP=$(date +%s)

# Guard: se as VKs ja foram geradas em uma execucao anterior, nao gera
# de novo. Para forcar regeneracao, defina FORCE_VK=1.
if [ "${FORCE_VK:-0}" != "1" ]; then
  EXISTING_PROC_VK=$(aws secretsmanager get-secret-value \
    --region "$AWS_REGION" \
    --secret-id "archlens/${ENVIRONMENT}/processing" \
    --query SecretString --output text 2>/dev/null | jq -r '.LLM_API_KEY // empty')

  if [ -n "$EXISTING_PROC_VK" ] && [ "$EXISTING_PROC_VK" != "null" ] \
     && [ "$EXISTING_PROC_VK" != "PLACEHOLDER" ]; then
    echo "✓ VK ja existe em archlens/${ENVIRONMENT}/processing (skip)."
    echo "  Para regenerar, rode com: FORCE_VK=1 $0"
    exit 0
  fi
fi

echo "▶ Aguardando LiteLLM ficar healthy"
for i in {1..30}; do
  if curl -fs "$LITELLM_URL/health" >/dev/null 2>&1; then
    break
  fi
  if [ "$i" -eq 30 ]; then
    echo "❌ LiteLLM nao respondeu em /health apos 30 tentativas"
    exit 1
  fi
  sleep 5
done
echo "  ✓ LiteLLM healthy"

echo "▶ Lendo MASTER_KEY do Secrets Manager"
MASTER_KEY=$(aws secretsmanager get-secret-value \
  --region "$AWS_REGION" \
  --secret-id "$LITELLM_SECRET" \
  --query SecretString --output text | jq -r '.MASTER_KEY')

if [ -z "$MASTER_KEY" ] || [ "$MASTER_KEY" = "null" ] || [ "$MASTER_KEY" = "PLACEHOLDER" ]; then
  echo "❌ MASTER_KEY nao preenchida em $LITELLM_SECRET"
  exit 1
fi

generate_vk() {
  local payload="$1"
  curl -fs -X POST "$LITELLM_URL/key/generate" \
    -H "Authorization: Bearer $MASTER_KEY" \
    -H "Content-Type: application/json" \
    -d "$payload" | jq -r '.key'
}

update_secret() {
  local secret_id="$1"
  local vk="$2"

  # Le o JSON atual, mescla LLM_API_KEY e regrava
  local current
  current=$(aws secretsmanager get-secret-value \
    --region "$AWS_REGION" \
    --secret-id "$secret_id" \
    --query SecretString --output text)

  local merged
  merged=$(echo "$current" | jq --arg vk "$vk" '. + {LLM_API_KEY: $vk}')

  aws secretsmanager put-secret-value \
    --region "$AWS_REGION" \
    --secret-id "$secret_id" \
    --secret-string "$merged" >/dev/null
}

echo "▶ Gerando VK processing-service"
PROC_VK=$(generate_vk "{
  \"key_alias\": \"processing-service-${TIMESTAMP}\",
  \"max_budget\": 10.0,
  \"budget_duration\": \"30d\",
  \"models\": [\"archlens-vision\",\"archlens-analyzer\"],
  \"rpm_limit\": 30,
  \"tpm_limit\": 100000,
  \"metadata\": {\"service\":\"processing-service\",\"env\":\"${ENVIRONMENT}\"}
}")
echo "  ✓ ${PROC_VK:0:10}…"

echo "▶ Gerando VK report-service"
REP_VK=$(generate_vk "{
  \"key_alias\": \"report-service-${TIMESTAMP}\",
  \"max_budget\": 5.0,
  \"budget_duration\": \"30d\",
  \"models\": [\"archlens-analyzer\"],
  \"rpm_limit\": 20,
  \"tpm_limit\": 50000,
  \"metadata\": {\"service\":\"report-service\",\"env\":\"${ENVIRONMENT}\"}
}")
echo "  ✓ ${REP_VK:0:10}…"

echo "▶ Atualizando $PROCESSING_SECRET"
update_secret "$PROCESSING_SECRET" "$PROC_VK"

echo "▶ Atualizando $REPORT_SECRET"
update_secret "$REPORT_SECRET" "$REP_VK"

echo "✅ Virtual Keys geradas e propagadas. Os servicos processing e report"
echo "   devem ser restartados apos um novo fetch-secrets para puxar as VKs:"
echo "     ./fetch-secrets.sh"
echo "     docker compose -f docker-compose.ec2.yml restart processing-service report-service"
