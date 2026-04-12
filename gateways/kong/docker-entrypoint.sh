#!/bin/bash
set -e

# Se KONG_JWT_SECRET está definida, usar o template com autenticação JWT
if [ -n "${KONG_JWT_SECRET:-}" ]; then
    echo "KONG_JWT_SECRET found — enabling JWT auth"
    sed "s|\${KONG_JWT_SECRET}|${KONG_JWT_SECRET}|g" /etc/kong/kong.yml.template > /tmp/kong.yml
else
    echo "KONG_JWT_SECRET not set — using config without auth"
    cp /etc/kong/kong.yml /tmp/kong.yml
fi

export KONG_DECLARATIVE_CONFIG=/tmp/kong.yml

exec /docker-entrypoint.sh kong docker-start
