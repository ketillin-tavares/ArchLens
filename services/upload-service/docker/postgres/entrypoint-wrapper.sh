#!/bin/bash
set -e

# Configura o New Relic Infrastructure Agent
cat > /etc/newrelic-infra.yml <<EOF
license_key: ${NRIA_LICENSE_KEY}
display_name: ${NRIA_DISPLAY_NAME:-upload-service-postgres}
EOF

# Configura a integração PostgreSQL do New Relic
mkdir -p /etc/newrelic-infra/integrations.d
cat > /etc/newrelic-infra/integrations.d/postgresql-config.yml <<EOF
integrations:
  - name: nri-postgresql
    env:
      USERNAME: ${POSTGRES_USER:-upload_user}
      PASSWORD: ${POSTGRES_PASSWORD:-upload_pass}
      HOSTNAME: localhost
      PORT: "5432"
      DATABASE: ${POSTGRES_DB:-upload_db}
      COLLECT_DB_LOCK_METRICS: "true"
      ENABLE_SSL: "false"
      COLLECTION_LIST: "ALL"
    interval: 15s
EOF

# Inicia o New Relic Infrastructure Agent somente após o PostgreSQL aceitar conexões
(
  until pg_isready -q; do
    sleep 2
  done
  /usr/bin/newrelic-infra
) &

# Delega para o entrypoint original do PostgreSQL
exec docker-entrypoint.sh "$@"
