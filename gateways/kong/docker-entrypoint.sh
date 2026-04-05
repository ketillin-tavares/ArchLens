#!/bin/bash
set -e

# Se KONG_API_KEY está definida, usar o template com autenticação
if [ -n "${KONG_API_KEY:-}" ]; then
    echo "KONG_API_KEY found — enabling key-auth"
    sed "s/\${KONG_API_KEY}/${KONG_API_KEY}/g" /etc/kong/kong.yml.template > /tmp/kong.yml
else
    echo "KONG_API_KEY not set — using config without auth"
    cp /etc/kong/kong.yml /tmp/kong.yml
fi

export KONG_DECLARATIVE_CONFIG=/tmp/kong.yml

exec /docker-entrypoint.sh kong docker-start
