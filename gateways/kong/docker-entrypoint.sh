#!/bin/bash
set -e

# Strip potential CRLF from env var (Windows .env files use CRLF)
KONG_JWT_SECRET=$(printf '%s' "${KONG_JWT_SECRET:-}" | tr -d '\r')
CLERK_ISSUER_URL=$(printf '%s' "${CLERK_ISSUER_URL:-}" | tr -d '\r')

# Se KONG_JWT_SECRET está definida, usar o template com autenticação JWT
if [ -n "${KONG_JWT_SECRET}" ]; then
    echo "KONG_JWT_SECRET found — enabling JWT auth"
    sed "s|\${KONG_JWT_SECRET}|${KONG_JWT_SECRET}|g; s|\${CLERK_ISSUER_URL}|${CLERK_ISSUER_URL}|g" /etc/kong/kong.yml.template > /tmp/kong.yml
else
    echo "KONG_JWT_SECRET not set — using config without auth"
    cp /etc/kong/kong.yml /tmp/kong.yml
fi

export KONG_DECLARATIVE_CONFIG=/tmp/kong.yml

exec /docker-entrypoint.sh kong docker-start
