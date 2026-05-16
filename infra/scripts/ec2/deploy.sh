#!/bin/bash
# ══════════════════════════════════════════════════════════════════════
#  deploy.sh — Update in-place. Chamado pelo GitHub Actions via SSH apos
#  build/push das imagens para o ECR.
#
#  NAO recria EC2. Garante que deps (rabbit/presidio/litellm) estao up,
#  roda migrations, sobe servicos com a nova tag.
#
#  Uso:
#    ./deploy.sh <commit-sha>
# ══════════════════════════════════════════════════════════════════════
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "Uso: $0 <commit-sha>"
  exit 1
fi

readonly COMMIT_SHA="$1"
readonly REPO_ROOT="/opt/archlens"
readonly COMPOSE_FILE="$REPO_ROOT/docker-compose.ec2.yml"

cd "$REPO_ROOT"

# set -a faz `source` exportar cada var automaticamente.
set -a
# shellcheck disable=SC1091
source "$REPO_ROOT/.bootstrap.env"
set +a

echo "▶ [1/7] Pull do commit $COMMIT_SHA"
git fetch --quiet origin
git checkout --quiet "$COMMIT_SHA"

echo "▶ [2/7] Login no ECR"
aws ecr get-login-password --region "$AWS_REGION" \
  | docker login --username AWS --password-stdin "$ECR_REGISTRY" >/dev/null

echo "▶ [3/7] Re-fetch de secrets"
"$REPO_ROOT/infra/scripts/ec2/fetch-secrets.sh"

export IMAGE_TAG="$COMMIT_SHA"

echo "▶ [4/7] Pull das imagens (tag=$COMMIT_SHA)"
docker compose -f "$COMPOSE_FILE" pull

echo "▶ [5/7] Garantindo deps up (rabbit/presidio/litellm)"
docker compose -f "$COMPOSE_FILE" up -d \
  rabbitmq presidio-analyzer presidio-anonymizer litellm

# Garante o user do RabbitMQ (load_definitions nao cria via env vars).
"$REPO_ROOT/infra/scripts/ec2/ensure-rabbit-user.sh"

# Espera litellm responder antes do VK bootstrap.
echo "  Aguardando litellm /health/liveliness..."
for i in {1..30}; do
  if curl -fs http://localhost:4000/health/liveliness >/dev/null 2>&1; then
    echo "  ✓ litellm pronto"
    break
  fi
  sleep 5
done

# Gera VKs se ainda nao existirem (script tem guard de idempotencia).
"$REPO_ROOT/infra/scripts/ec2/bootstrap-litellm-vk.sh" || true

# Re-fetch caso VKs tenham acabado de ser geradas.
"$REPO_ROOT/infra/scripts/ec2/fetch-secrets.sh"

echo "▶ [6/7] Rodando migrations"
docker compose -f "$COMPOSE_FILE" run --rm upload-migrations
docker compose -f "$COMPOSE_FILE" run --rm processing-migrations
docker compose -f "$COMPOSE_FILE" run --rm report-migrations

echo "▶ [7/7] Up de todos os servicos (recreate apenas com imagem nova)"
docker compose -f "$COMPOSE_FILE" up -d --remove-orphans

echo "▶ Limpando imagens antigas"
docker image prune -f >/dev/null

echo "✅ Deploy do commit $COMMIT_SHA concluido"
docker compose -f "$COMPOSE_FILE" ps
