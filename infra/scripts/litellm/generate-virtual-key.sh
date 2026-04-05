#!/bin/bash
set -e

LITELLM_URL="${LITELLM_URL:-http://localhost:4000}"
LITELLM_MASTER_KEY="${LITELLM_MASTER_KEY:-sk-archlens-dev}"

echo "=== Gerando virtual key para processing-service ==="

RESPONSE=$(curl -s -X POST "${LITELLM_URL}/key/generate" \
  -H "Authorization: Bearer ${LITELLM_MASTER_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "key_alias": "processing-service",
    "max_budget": 10.0,
    "budget_duration": "30d",
    "models": ["archlens-vision", "archlens-analyzer"],
    "rpm_limit": 30,
    "tpm_limit": 100000,
    "metadata": {"service": "processing-service", "env": "dev"}
  }')

echo "$RESPONSE" | python -m json.tool

KEY=$(echo "$RESPONSE" | python -c "import sys,json; print(json.load(sys.stdin)['key'])" 2>/dev/null)

if [ -n "$KEY" ]; then
    echo ""
    echo "=== Virtual key gerada ==="
    echo "LITELLM_API_KEY=${KEY}"
    echo ""
    echo "Adicione ao .env do processing-service:"
    echo "  LLM_API_KEY=${KEY}"
fi
