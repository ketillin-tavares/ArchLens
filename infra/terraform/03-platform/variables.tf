# ── General ────────────────────────────────────────────────────────────
variable "aws_region" {
  type        = string
  default     = "us-east-2"
  description = "Região AWS — deve ser a mesma dos workspaces 01-foundation e 02-cluster"
}

variable "environment" {
  type        = string
  default     = "dev"
  description = "Nome do ambiente (dev, staging, prod) — usado em tags para cost tracking e auditoria"
}

# ── Vault ──────────────────────────────────────────────────────────────
variable "vault_chart_version" {
  type        = string
  default     = "0.32.0"
  description = "Versão do Helm chart do HashiCorp Vault"
}

variable "vault_storage_size" {
  type        = string
  default     = "5Gi"
  description = "Tamanho do PVC para persistência do Vault"
}

variable "vault_storage_class" {
  type        = string
  default     = "gp2"
  description = "StorageClass do PVC do Vault (gp2 para EBS)"
}

variable "vault_service_type" {
  type        = string
  default     = "LoadBalancer"
  description = "Tipo do Service do Vault — LoadBalancer para bootstrap, ClusterIP após configuração"
}

# ── RabbitMQ ───────────────────────────────────────────────────────────
variable "rabbitmq_chart_version" {
  type        = string
  default     = "16.0.14"
  description = "Versão do Helm chart Bitnami do RabbitMQ"
}

variable "rabbitmq_password" {
  type        = string
  sensitive   = true
  description = "Senha do RabbitMQ — configurar como variável sensível no Terraform Cloud"
}

variable "rabbitmq_erlang_cookie" {
  type        = string
  sensitive   = true
  description = "Erlang cookie do RabbitMQ — string aleatória (openssl rand -hex 32)"
}

variable "rabbitmq_storage_size" {
  type        = string
  default     = "2Gi"
  description = "Tamanho do PVC para persistência do RabbitMQ. 2Gi é suficiente: as filas são durável/transientes e não armazenam payloads grandes (apenas metadata de analises)"
}

# ── Kong ───────────────────────────────────────────────────────────────
variable "kong_chart_version" {
  type        = string
  default     = "0.24.0"
  description = "Versão do Helm chart do Kong Ingress Controller"
}

# ── LiteLLM ────────────────────────────────────────────────────────────
variable "litellm_image" {
  type        = string
  default     = "ghcr.io/berriai/litellm:v1.83.2-nightly"
  description = "Imagem Docker do LiteLLM Proxy — SEMPRE usar tag fixa versionada (alinhada com gateways/litellm/Dockerfile)"
}

variable "litellm_db_password" {
  type        = string
  sensitive   = true
  description = "Senha do usuario litellm_user no RDS (criado pelo kubernetes_job litellm-db-bootstrap e usado pela LITELLM_DATABASE_URL)"
}

# ── New Relic ──────────────────────────────────────────────────────────
variable "newrelic_license_key" {
  type        = string
  sensitive   = true
  description = "New Relic Ingest License Key — configurar como variável sensível no Terraform Cloud"
}

variable "newrelic_chart_version" {
  type        = string
  default     = "7.0.6"
  description = "Versão do Helm chart nri-bundle do New Relic"
}

variable "db_password" {
  type        = string
  sensitive   = true
  description = "Senha do RDS PostgreSQL — usada pela integração nri-postgresql do New Relic"
}
