setup:
	docker compose up -d --build
	bash infra/scripts/litellm/generate-virtual-key.sh
	@echo ""
	@echo "=== ArchLens rodando ==="
	@echo "Kong Gateway:  http://localhost:8000"
	@echo "Kong Manager:  http://localhost:8002"
	@echo "LiteLLM UI:    http://localhost:4000/ui"
	@echo "RabbitMQ UI:   http://localhost:15672"

up:
	docker compose up -d --build

down:
	docker compose down

rebuild-services:
	docker compose up -d --build upload-service processing-service report-service

down-clean:
	docker compose down -v

logs:
	docker compose logs -f

logs-upload:
	docker compose logs -f upload-service

logs-processing:
	docker compose logs -f processing-service

logs-report:
	docker compose logs -f report-service

psql-upload:
	docker compose exec postgres psql -U archlens -d upload_db

psql-processing:
	docker compose exec postgres psql -U archlens -d processing_db

psql-report:
	docker compose exec postgres psql -U archlens -d report_db

rabbitmq-ui:
	@echo "RabbitMQ Management: http://localhost:15672 (archlens/archlens_dev)"

vault-ui:
	@echo "Vault UI: http://localhost:8200 (token: archlens-dev-token)"

vault-init:
	bash infra/scripts/vault/init-vault.sh

vault-secrets:
	@echo "=== Kong ===" && vault kv get secret/archlens/kong
	@echo "=== LiteLLM ===" && vault kv get secret/archlens/litellm
	@echo "=== Database ===" && vault kv get secret/archlens/database
	@echo "=== RabbitMQ ===" && vault kv get secret/archlens/rabbitmq
	@echo "=== New Relic ===" && vault kv get secret/archlens/newrelic

kong-status:
	curl -s http://localhost:8001/status | python -m json.tool

kong-services:
	curl -s http://localhost:8001/services | python -m json.tool

kong-routes:
	curl -s http://localhost:8001/routes | python -m json.tool

litellm-generate-key:
	bash infra/scripts/litellm/generate-virtual-key.sh

litellm-ui:
	@echo "LiteLLM UI: http://localhost:4000/ui"

venv-us:
	cd services/upload-service && source .venv/Scripts/activate

venv-ps:
	cd services/processing-service && source .venv/Scripts/activate

venv-rs:
	cd services/report-service && source .venv/Scripts/activate
