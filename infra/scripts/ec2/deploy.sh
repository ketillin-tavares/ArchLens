#!/bin/bash
# ══════════════════════════════════════════════════════════════════════
#  deploy.sh — Update in-place dos servicos. Chamado pelo GitHub Actions
#  via SSH apos build/push das imagens para o ECR.
#
#  NAO recria EC2, NAO mexe em RDS, RabbitMQ ou LiteLLM. Apenas atualiza
#  imagens dos servicos backend e do frontend.
#
#  Uso:
#    ./deploy.sh <commit-sha>
#
#  Pre-requisitos:
#    - Repo clonado em /opt/archlens
#    - .bootstrap.env presente com ECR_REGISTRY
#    - Imagens ja publicadas no ECR com a tag <commit-sha>
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

# shellcheck source=/dev/null
source "$REPO_ROOT/.bootstrap.env"

echo "▶ [1/6] Pull do commit $COMMIT_SHA"
git fetch --quiet origin
git checkout --quiet "$COMMIT_SHA"

echo "▶ [2/6] Login no ECR"
aws ecr get-login-password --region "$AWS_REGION" \
  | docker login --username AWS --password-stdin "$ECR_REGISTRY" >/dev/null

echo "▶ [3/6] Re-fetch de secrets"
"$REPO_ROOT/infra/scripts/ec2/fetch-secrets.sh"

# Exporta IMAGE_TAG para o compose
export ECR_REGISTRY
export IMAGE_TAG="$COMMIT_SHA"

echo "▶ [4/6] Pull das imagens novas"
docker compose -f "$COMPOSE_FILE" pull \
  upload-service processing-service report-service frontend litellm

echo "▶ [5/6] Rodando migrations"
docker compose -f "$COMPOSE_FILE" run --rm upload-migrations
docker compose -f "$COMPOSE_FILE" run --rm processing-migrations
docker compose -f "$COMPOSE_FILE" run --rm report-migrations

echo "▶ [6/6] Update in-place dos servicos (--no-deps preserva infra)"
docker compose -f "$COMPOSE_FILE" up -d --no-deps --remove-orphans \
  litellm \
  upload-service \
  processing-service \
  report-service \
  frontend

echo "▶ Limpando imagens antigas"
docker image prune -f >/dev/null

echo "✅ Deploy do commit $COMMIT_SHA concluido"
docker compose -f "$COMPOSE_FILE" ps
