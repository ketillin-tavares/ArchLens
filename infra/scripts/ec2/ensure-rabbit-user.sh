#!/bin/bash
# ══════════════════════════════════════════════════════════════════════
#  ensure-rabbit-user.sh — Garante que o user do RabbitMQ existe com a
#  senha do Secrets Manager. Idempotente.
#
#  Necessario porque com `management.load_definitions` configurado, o
#  RabbitMQ NAO cria o user automaticamente a partir das env vars
#  RABBITMQ_DEFAULT_USER/PASS. Como removemos `users[]` do definitions
#  (pra evitar password hardcoded), precisamos criar via rabbitmqctl.
#
#  Pre-requisitos:
#    - Container `rabbitmq` rodando e healthy
#    - /opt/archlens/secrets/rabbitmq.env preenchido (via fetch-secrets)
# ══════════════════════════════════════════════════════════════════════
set -euo pipefail

readonly SECRETS_FILE="/opt/archlens/secrets/rabbitmq.env"

if [ ! -f "$SECRETS_FILE" ]; then
  echo "❌ $SECRETS_FILE nao existe. Rode fetch-secrets.sh antes."
  exit 1
fi

# shellcheck disable=SC1090
source "$SECRETS_FILE"

readonly USER="${RABBITMQ_DEFAULT_USER:?RABBITMQ_DEFAULT_USER ausente em $SECRETS_FILE}"
readonly PASS="${RABBITMQ_DEFAULT_PASS:?RABBITMQ_DEFAULT_PASS ausente em $SECRETS_FILE}"

echo "▶ Aguardando RabbitMQ ficar disponivel"
for i in {1..30}; do
  if docker exec rabbitmq rabbitmq-diagnostics -q ping >/dev/null 2>&1; then
    break
  fi
  if [ "$i" -eq 30 ]; then
    echo "❌ RabbitMQ nao respondeu em 5 minutos"
    exit 1
  fi
  sleep 10
done

echo "▶ Garantindo user '$USER' (idempotente)"
if docker exec rabbitmq rabbitmqctl authenticate_user "$USER" "$PASS" >/dev/null 2>&1; then
  echo "  ✓ User ja autentica corretamente"
  exit 0
fi

# Tenta criar; se ja existe, muda a senha
if docker exec rabbitmq rabbitmqctl add_user "$USER" "$PASS" 2>/dev/null; then
  echo "  ✓ User '$USER' criado"
else
  docker exec rabbitmq rabbitmqctl change_password "$USER" "$PASS" >/dev/null
  echo "  ✓ Senha do user '$USER' atualizada"
fi

docker exec rabbitmq rabbitmqctl set_user_tags "$USER" administrator >/dev/null
docker exec rabbitmq rabbitmqctl set_permissions -p / "$USER" ".*" ".*" ".*" >/dev/null

# Validacao final
docker exec rabbitmq rabbitmqctl authenticate_user "$USER" "$PASS" >/dev/null
echo "  ✓ Auth validado"
