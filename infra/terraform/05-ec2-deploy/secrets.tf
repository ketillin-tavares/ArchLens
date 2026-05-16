# Cria os secrets vazios (placeholder JSON). Os valores reais devem ser
# preenchidos manualmente via AWS Console ou CLI apos o terraform apply.
# Ver docs/deploy_ec2_guide.md para o formato esperado de cada secret.

locals {
  secret_names = [
    "database",
    "rabbitmq",
    "aws",
    "clerk",
    "newrelic",
    "litellm",
    "processing",
    "report",
    "kong",
  ]

  secret_placeholders = {
    database   = jsonencode({ host = "PLACEHOLDER", port = "5432", master_user = "archlens", master_password = "PLACEHOLDER", upload_user = "upload_user", upload_password = "PLACEHOLDER", processing_user = "processing_user", processing_password = "PLACEHOLDER", report_user = "report_user", report_password = "PLACEHOLDER", litellm_user = "litellm_user", litellm_password = "PLACEHOLDER" })
    rabbitmq   = jsonencode({ user = "archlens", password = "PLACEHOLDER" })
    aws        = jsonencode({ s3_bucket_name = "PLACEHOLDER", region = "us-east-2" })
    clerk      = jsonencode({ CLERK_ISSUER_URL = "PLACEHOLDER", CLERK_JWT_TEMPLATE = "archlens", VITE_CLERK_PUBLISHABLE_KEY = "PLACEHOLDER" })
    newrelic   = jsonencode({ license_key = "PLACEHOLDER", account_id = "PLACEHOLDER", user_key = "PLACEHOLDER" })
    litellm    = jsonencode({ MASTER_KEY = "PLACEHOLDER", gemini_api_key = "PLACEHOLDER" })
    processing = jsonencode({ LLM_API_KEY = "PLACEHOLDER" })
    report     = jsonencode({ LLM_API_KEY = "PLACEHOLDER" })
    kong       = jsonencode({ KONG_JWT_SECRET = "PLACEHOLDER" })
  }
}

resource "aws_secretsmanager_secret" "archlens" {
  for_each = toset(local.secret_names)

  name                    = "archlens/${var.environment}/${each.key}"
  description             = "ArchLens ${each.key} secrets para o ambiente ${var.environment}"
  recovery_window_in_days = 0 # permite recriar imediatamente em dev

  tags = local.common_tags
}

resource "aws_secretsmanager_secret_version" "archlens" {
  for_each = aws_secretsmanager_secret.archlens

  secret_id     = each.value.id
  secret_string = local.secret_placeholders[each.key]

  lifecycle {
    # Nao sobrescreve valores reais ja preenchidos pelo operador.
    ignore_changes = [secret_string]
  }
}
