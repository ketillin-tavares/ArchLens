#!/bin/bash
# ══════════════════════════════════════════════════════════════════════
#  bootstrap-rds.sh — Cria os 4 databases e users no RDS, idempotente.
#  Equivalente ao init-multiple-dbs.sh do compose dev, mas roda contra
#  uma instancia RDS existente em vez de container postgres local.
#
#  Pre-requisitos:
#    - psql instalado no host
#    - .bootstrap.env carregado (RDS_HOST, RDS_MASTER_PASSWORD)
#    - Secret archlens/<env>/database preenchido com as senhas dos 4 users
#
#  Uso:
#    ./bootstrap-rds.sh
# ══════════════════════════════════════════════════════════════════════
set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

# shellcheck source=/dev/null
source "$REPO_ROOT/.bootstrap.env"

: "${AWS_REGION:?AWS_REGION nao definido}"
: "${ENVIRONMENT:?ENVIRONMENT nao definido}"
: "${RDS_HOST:?RDS_HOST nao definido}"
: "${RDS_MASTER_PASSWORD:?RDS_MASTER_PASSWORD nao definido}"

readonly DB_SECRET="archlens/${ENVIRONMENT}/database"

echo "▶ Aguardando RDS aceitar conexoes em $RDS_HOST:5432"
for i in {1..30}; do
  if pg_isready -h "$RDS_HOST" -U archlens -q -t 5; then
    echo "  ✓ RDS pronto"
    break
  fi
  if [ "$i" -eq 30 ]; then
    echo "❌ RDS nao respondeu em 5 minutos"
    exit 1
  fi
  sleep 10
done

echo "▶ Buscando senhas dos users no Secrets Manager"
DB_JSON=$(aws secretsmanager get-secret-value \
  --region "$AWS_REGION" \
  --secret-id "$DB_SECRET" \
  --query SecretString --output text)

UPLOAD_PASS=$(echo "$DB_JSON"     | jq -r '.upload_password')
PROCESSING_PASS=$(echo "$DB_JSON" | jq -r '.processing_password')
REPORT_PASS=$(echo "$DB_JSON"     | jq -r '.report_password')
LITELLM_PASS=$(echo "$DB_JSON"    | jq -r '.litellm_password')

for var in UPLOAD_PASS PROCESSING_PASS REPORT_PASS LITELLM_PASS; do
  if [ "${!var}" = "PLACEHOLDER" ] || [ -z "${!var}" ] || [ "${!var}" = "null" ]; then
    echo "❌ $var nao foi preenchido no secret $DB_SECRET"
    exit 1
  fi
done

export PGPASSWORD="$RDS_MASTER_PASSWORD"

create_user_and_db() {
  local db="$1"
  local user="$2"
  local pass="$3"

  echo "▶ Garantindo user '$user' e database '$db'"

  # PG16+ exige que o master user (archlens) tenha o role do dono concedido
  # antes de criar um DB com OWNER outro_role. No RDS, o master nao e true
  # superuser, entao precisamos do GRANT explicito.
  psql -v ON_ERROR_STOP=1 -h "$RDS_HOST" -U archlens -d archlens <<SQL
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '$user') THEN
    CREATE ROLE $user LOGIN PASSWORD '$pass';
  ELSE
    ALTER ROLE $user WITH PASSWORD '$pass';
  END IF;
END
\$\$;

GRANT $user TO archlens;
SQL

  if ! psql -h "$RDS_HOST" -U archlens -d archlens -tAc \
       "SELECT 1 FROM pg_database WHERE datname = '$db'" | grep -q 1; then
    psql -v ON_ERROR_STOP=1 -h "$RDS_HOST" -U archlens -d archlens \
      -c "CREATE DATABASE $db OWNER $user"
  fi

  psql -v ON_ERROR_STOP=1 -h "$RDS_HOST" -U archlens -d archlens \
    -c "GRANT ALL PRIVILEGES ON DATABASE $db TO $user"
}

create_user_and_db "upload_db"     "upload_user"     "$UPLOAD_PASS"
create_user_and_db "processing_db" "processing_user" "$PROCESSING_PASS"
create_user_and_db "report_db"     "report_user"     "$REPORT_PASS"
create_user_and_db "litellm_db"    "litellm_user"    "$LITELLM_PASS"

unset PGPASSWORD
echo "✅ RDS bootstrap concluido (4 DBs + users)"
