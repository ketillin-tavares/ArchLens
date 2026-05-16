#!/bin/bash
# ══════════════════════════════════════════════════════════════════════
#  fetch-secrets.sh — Le secrets do AWS Secrets Manager e gera os
#  arquivos .env por servico em /opt/archlens/secrets/.
#
#  Idempotente: pode ser executado quantas vezes quiser. Sobrescreve
#  os .env existentes com os valores atuais dos secrets.
#
#  Pre-requisitos:
#    - aws CLI instalado
#    - jq instalado
#    - .bootstrap.env carregado (AWS_REGION, ENVIRONMENT, RDS_HOST,
#      S3_BUCKET)
#    - IAM role da EC2 com permissao secretsmanager:GetSecretValue
# ══════════════════════════════════════════════════════════════════════
set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
readonly SECRETS_DIR="$REPO_ROOT/secrets"

# shellcheck source=/dev/null
source "$REPO_ROOT/.bootstrap.env"

: "${AWS_REGION:?AWS_REGION nao definido}"
: "${ENVIRONMENT:?ENVIRONMENT nao definido}"
: "${RDS_HOST:?RDS_HOST nao definido}"
: "${S3_BUCKET:?S3_BUCKET nao definido}"
: "${ECR_REGISTRY:?ECR_REGISTRY nao definido}"

mkdir -p "$SECRETS_DIR"
chmod 700 "$SECRETS_DIR"

# Helper: le um secret e retorna o JSON
fetch() {
  aws secretsmanager get-secret-value \
    --region "$AWS_REGION" \
    --secret-id "archlens/${ENVIRONMENT}/$1" \
    --query SecretString --output text
}

echo "▶ Buscando secrets de archlens/${ENVIRONMENT}/*"
DB_JSON=$(fetch database)
RABBITMQ_JSON=$(fetch rabbitmq)
CLERK_JSON=$(fetch clerk)
NEWRELIC_JSON=$(fetch newrelic)
LITELLM_JSON=$(fetch litellm)
PROCESSING_JSON=$(fetch processing)
REPORT_JSON=$(fetch report)
KONG_JSON=$(fetch kong)

# ── Helpers de extracao ─────────────────────────────────────────────────
# Cada helper retorna string vazia (e avisa em stderr) se o valor estiver
# null/missing — evita escrever literal "null" no .env. Sentinel
# "PLACEHOLDER" e tratado como vazio com warning explicito.
extract() {
  local json="$1"
  local key="$2"
  local name="$3"
  local val
  val=$(echo "$json" | jq -r ".$key // empty")
  if [ -z "$val" ] || [ "$val" = "null" ]; then
    echo "  ⚠️  $name.$key vazio/null em secrets" >&2
    val=""
  elif [ "$val" = "PLACEHOLDER" ]; then
    echo "  ⚠️  $name.$key esta PLACEHOLDER (preencher no Secrets Manager)" >&2
  fi
  printf '%s' "$val"
}

db()         { extract "$DB_JSON"         "$1" "database"; }
rmq()        { extract "$RABBITMQ_JSON"   "$1" "rabbitmq"; }
clerk()      { extract "$CLERK_JSON"      "$1" "clerk"; }
nr()         { extract "$NEWRELIC_JSON"   "$1" "newrelic"; }
litellm()    { extract "$LITELLM_JSON"    "$1" "litellm"; }
processing() { extract "$PROCESSING_JSON" "$1" "processing"; }
report()     { extract "$REPORT_JSON"     "$1" "report"; }
kong()       { extract "$KONG_JSON"       "$1" "kong"; }

# ── upload-service.env ─────────────────────────────────────────────────
# Nota: S3_ENDPOINT_URL vazio sinaliza ao S3Settings.is_local que estamos
# em S3 real. Sem AWS_ACCESS_KEY_ID/SECRET — boto3 usa IAM role da EC2.
echo "▶ Gerando upload-service.env"
cat > "$SECRETS_DIR/upload-service.env" <<EOF
DATABASE_HOST=$RDS_HOST
DATABASE_PORT=5432
DATABASE_USER=$(db upload_user)
DATABASE_PASSWORD=$(db upload_password)
DATABASE_NAME=upload_db

RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USER=$(rmq user)
RABBITMQ_PASSWORD=$(rmq password)
RABBITMQ_EXCHANGE_NAME=analise.events
RABBITMQ_QUEUE_NAME=upload-service.status-updates

S3_ENDPOINT_URL=
S3_BUCKET_NAME=$S3_BUCKET
AWS_REGION=$AWS_REGION

SERVICE_NAME=upload-service
DEBUG=false
LOG_LEVEL=INFO

NEW_RELIC_USER_KEY=$(nr user_key)
NEW_RELIC_LICENSE_KEY=$(nr license_key)
NEW_RELIC_ACCOUNT_ID=$(nr account_id)
NRIA_DISPLAY_NAME=upload-service
NRIA_LICENSE_KEY=$(nr license_key)
EOF

# ── processing-service.env ─────────────────────────────────────────────
echo "▶ Gerando processing-service.env"
cat > "$SECRETS_DIR/processing-service.env" <<EOF
DATABASE_HOST=$RDS_HOST
DATABASE_PORT=5432
DATABASE_USER=$(db processing_user)
DATABASE_PASSWORD=$(db processing_password)
DATABASE_NAME=processing_db

RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USER=$(rmq user)
RABBITMQ_PASSWORD=$(rmq password)
RABBITMQ_EXCHANGE_NAME=analise.events
RABBITMQ_QUEUE_NAME=processing-service.pipeline

S3_ENDPOINT_URL=
S3_BUCKET_NAME=$S3_BUCKET
AWS_REGION=$AWS_REGION

LLM_BASE_URL=http://litellm:4000
LLM_API_KEY=$(processing LLM_API_KEY)
LLM_MODEL_NAME=archlens-vision
LLM_ANALYZER_MODEL_NAME=archlens-analyzer
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=4096

ENABLE_MULTIAGENT=true
ENABLE_JUDGE=false

SERVICE_NAME=processing-service
DEBUG=false
LOG_LEVEL=INFO

NEW_RELIC_USER_KEY=$(nr user_key)
NEW_RELIC_LICENSE_KEY=$(nr license_key)
NEW_RELIC_ACCOUNT_ID=$(nr account_id)
NRIA_DISPLAY_NAME=processing-service
NRIA_LICENSE_KEY=$(nr license_key)
EOF

# ── report-service.env ─────────────────────────────────────────────────
echo "▶ Gerando report-service.env"
cat > "$SECRETS_DIR/report-service.env" <<EOF
DATABASE_HOST=$RDS_HOST
DATABASE_PORT=5432
DATABASE_USER=$(db report_user)
DATABASE_PASSWORD=$(db report_password)
DATABASE_NAME=report_db

RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USER=$(rmq user)
RABBITMQ_PASSWORD=$(rmq password)
RABBITMQ_EXCHANGE_NAME=analise.events
RABBITMQ_QUEUE_NAME=report-service.reports

S3_ENDPOINT_URL=
S3_BUCKET_NAME=$S3_BUCKET
AWS_REGION=$AWS_REGION

LLM_BASE_URL=http://litellm:4000
LLM_API_KEY=$(report LLM_API_KEY)
LLM_MODEL_NAME=archlens-analyzer

SERVICE_NAME=report-service
DEBUG=false
LOG_LEVEL=INFO

NEW_RELIC_USER_KEY=$(nr user_key)
NEW_RELIC_LICENSE_KEY=$(nr license_key)
NEW_RELIC_ACCOUNT_ID=$(nr account_id)
NRIA_DISPLAY_NAME=report-service
NRIA_LICENSE_KEY=$(nr license_key)
EOF

# ── litellm.env ────────────────────────────────────────────────────────
echo "▶ Gerando litellm.env"
cat > "$SECRETS_DIR/litellm.env" <<EOF
LITELLM_DATABASE_URL=postgresql://litellm_user:$(db litellm_password)@$RDS_HOST:5432/litellm_db
LITELLM_MASTER_KEY=$(litellm MASTER_KEY)
STORE_MODEL_IN_DB=True
GEMINI_API_KEY=$(litellm gemini_api_key)
EOF

# ── rabbitmq.env ───────────────────────────────────────────────────────
echo "▶ Gerando rabbitmq.env"
cat > "$SECRETS_DIR/rabbitmq.env" <<EOF
RABBITMQ_DEFAULT_USER=$(rmq user)
RABBITMQ_DEFAULT_PASS=$(rmq password)
EOF

# ── kong.env ───────────────────────────────────────────────────────────
# KONG_JWT_SECRET: secret HS256 usado pelo plugin jwt do Kong para validar
# os tokens emitidos pelo Clerk. Lido pelo docker-entrypoint.sh do Kong.
echo "▶ Gerando kong.env"
cat > "$SECRETS_DIR/kong.env" <<EOF
KONG_JWT_SECRET=$(kong KONG_JWT_SECRET)
CLERK_ISSUER_URL=$(clerk CLERK_ISSUER_URL)
EOF

# ── newrelic.env ───────────────────────────────────────────────────────
echo "▶ Gerando newrelic.env"
cat > "$SECRETS_DIR/newrelic.env" <<EOF
NRIA_LICENSE_KEY=$(nr license_key)
NEW_RELIC_LICENSE_KEY=$(nr license_key)
NEW_RELIC_ACCOUNT_ID=$(nr account_id)
EOF

chmod 600 "$SECRETS_DIR"/*.env

echo "✅ Secrets escritos em $SECRETS_DIR ($(ls -1 "$SECRETS_DIR" | wc -l) arquivos)"
