#!/bin/bash
set -e

echo "=== Aguardando Ollama iniciar... ==="
until curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; do
    sleep 2
done

echo "=== Baixando gemma3:4b (vision + text, ~3.3 GB)... ==="
docker compose exec ollama ollama pull gemma3:4b

echo "=== Baixando gemma3:1b (text-only, ~1 GB)... ==="
docker compose exec ollama ollama pull gemma3:1b

echo "=== Modelos disponíveis: ==="
docker compose exec ollama ollama list

echo ""
echo "=== Ollama pronto! ==="
echo "Teste: curl http://localhost:11434/api/chat -d '{\"model\":\"gemma3:4b\",\"messages\":[{\"role\":\"user\",\"content\":\"Olá\"}],\"stream\":false}'"
