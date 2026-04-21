variable "aws_region" {
  type        = string
  default     = "us-east-2"
  description = "Região AWS do bucket S3 (CloudFront é global)"
}

variable "environment" {
  type        = string
  default     = "prod"
  description = "Nome do ambiente (dev, staging, prod) — usado em nomes e tags"
}

variable "api_gateway_url" {
  type        = string
  default     = ""
  description = <<-EOT
    URL pública do Kong API Gateway (esquema + host, sem path).
    Ex: https://kong-xxxxxx.elb.us-east-2.amazonaws.com
    Override manual — quando vazio, o valor vem do output kong_proxy_url
    do workspace archlens-platform via terraform_remote_state.
    Usada apenas na diretiva connect-src do CSP — o frontend lê via VITE_KONG_BASE_URL no build.
  EOT
}

variable "price_class" {
  type        = string
  default     = "PriceClass_100"
  description = "CloudFront price class. PriceClass_100 = US+EU+BR (mais barato)"
}

variable "waf_web_acl_arn" {
  type        = string
  default     = null
  description = "ARN de um WAFv2 Web ACL (global/CloudFront) opcional"
}

variable "enable_access_logs" {
  type        = bool
  default     = true
  description = "Se true, cria bucket *-logs e habilita logging da distribuição CloudFront."
}

variable "log_retention_days" {
  type        = number
  default     = 90
  description = "Dias até a expiração dos access logs no S3 (lifecycle). Default 90d."
}

variable "enable_origin_shield" {
  type        = bool
  default     = false
  description = "Liga Origin Shield na origem S3 (melhora cache hit ratio em alto tráfego)."
}

variable "origin_shield_region" {
  type        = string
  default     = "us-east-1"
  description = "Região do Origin Shield. Escolha a região AWS mais próxima dos usuários."
}

# ══════════════════════════════════════════════════════════════════════
#  Build-time secrets — gravados no SSM Parameter Store
#  O workflow frontend-deploy.yaml lê esses valores via aws ssm.
# ══════════════════════════════════════════════════════════════════════
variable "clerk_publishable_key" {
  type        = string
  sensitive   = true
  description = <<-EOT
    Clerk publishable key. Começa com pk_test_ (dev) ou pk_live_ (prod).
    Obter em: Clerk Dashboard > sua app > API Keys > "Publishable key".
    A key já contém (em base64) o Frontend API host que o SDK usa — não é
    necessário configurar URL do Clerk em lugar nenhum.
  EOT
}
