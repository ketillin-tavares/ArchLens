#!/bin/bash
set -e

VAULT_CONTAINER="vault"
VAULT_ADDR="http://127.0.0.1:8200"
VAULT_TOKEN="archlens-dev-token"

echo "=== Populando secrets no Vault ==="

# Carregar do .env se existir
if [ -f .env ]; then
    source .env
fi

run_vault() {
    docker exec -e VAULT_ADDR="$VAULT_ADDR" -e VAULT_TOKEN="$VAULT_TOKEN" "$VAULT_CONTAINER" vault "$@"
}

run_vault kv put secret/archlens/kong \
  API_KEY="${KONG_API_KEY:-archlens-api-key-dev}"

run_vault kv put secret/archlens/litellm \
  ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-change-me}" \
  OPENAI_API_KEY="${OPENAI_API_KEY:-change-me}" \
  MASTER_KEY="${LITELLM_MASTER_KEY:-sk-archlens-dev}"

run_vault kv put secret/archlens/database \
  PASSWORD="${POSTGRES_PASSWORD:-archlens_dev}"

run_vault kv put secret/archlens/rabbitmq \
  PASSWORD="${RABBITMQ_DEFAULT_PASS:-archlens_dev}"

run_vault kv put secret/archlens/newrelic \
  LICENSE_KEY="${NEW_RELIC_LICENSE_KEY:-change-me}"

echo "=== Configurando AppRole ==="

docker exec -e VAULT_ADDR="$VAULT_ADDR" -e VAULT_TOKEN="$VAULT_TOKEN" "$VAULT_CONTAINER" \
  sh -c 'echo "path \"secret/data/archlens/*\" { capabilities = [\"read\"] }" | vault policy write archlens-ci -'

run_vault auth enable approle 2>/dev/null || echo "AppRole already enabled"

run_vault write auth/approle/role/archlens-ci \
  token_policies="archlens-ci" \
  token_ttl=10m \
  token_max_ttl=15m \
  secret_id_ttl=0

echo ""
echo "=== Role ID ==="
run_vault read -field=role_id auth/approle/role/archlens-ci/role-id

echo ""
echo "=== Secret ID ==="
run_vault write -f -field=secret_id auth/approle/role/archlens-ci/secret-id

echo ""
echo "=== Vault setup complete ==="
echo "UI: http://localhost:8200 (token: archlens-dev-token)"
