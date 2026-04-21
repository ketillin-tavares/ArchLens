# ══════════════════════════════════════════════════════════════════════
#  archlens-frontend — S3 + CloudFront (sem domínio customizado)
#  Pattern: SPA Vite servida pela CloudFront com origem S3 privada via
#  Origin Access Control (OAC). Sem ACM/Route53 — usa o domínio default
#  *.cloudfront.net com certificado gerenciado pela AWS (grátis).
# ══════════════════════════════════════════════════════════════════════
terraform {
  required_version = ">= 1.5"

  cloud {
    organization = "archlens"
    workspaces { name = "archlens-frontend" }
  }

  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
}

provider "aws" {
  region = var.aws_region
}

# ── Remote state do workspace platform ───────────────────────────────
# Fonte da verdade para o URL do Kong API Gateway (Load Balancer criado
# pelo Ingress Controller). Evita drift silencioso: quando a plataforma
# recria o Ingress, o DNS do LB muda, e sem esta leitura o workspace
# frontend continua gravando o valor antigo no SSM.
data "terraform_remote_state" "platform" {
  backend = "remote"
  config = {
    organization = "archlens"
    workspaces   = { name = "archlens-platform" }
  }
}

locals {
  common_tags = {
    Project     = "archlens"
    Component   = "frontend"
    ManagedBy   = "terraform"
    Environment = var.environment
  }

  bucket_name = "archlens-frontend-${var.environment}"
  ssm_prefix  = "/archlens/frontend/${var.environment}"

  # Prioriza var.api_gateway_url (override manual); caso vazio, resolve
  # a partir do output kong_url do workspace platform (fonte de verdade
  # do LB do Kong Ingress).
  api_gateway_url = coalesce(
    var.api_gateway_url,
    try(data.terraform_remote_state.platform.outputs.kong_url, ""),
  )
}
