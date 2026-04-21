# ══════════════════════════════════════════════════════════════════════
#  Parameter Store — fonte única das chaves de build do frontend
#  O workflow de deploy lê estes valores via `aws ssm get-parameter` no
#  momento do build, eliminando a necessidade de configurá-los no
#  GitHub Secrets. Alterou a chave? `terraform apply` e rode o workflow —
#  o próximo deploy já pega o novo valor.
#
#  Observação de segurança: a Clerk publishable key é "publicly exposable"
#  (acaba embutida no bundle JS do browser — é projetada para isso).
#  Mesmo assim armazenamos como SecureString por consistência e para
#  restringir leitura via IAM.
# ══════════════════════════════════════════════════════════════════════

resource "aws_ssm_parameter" "clerk_publishable_key" {
  name        = "${local.ssm_prefix}/clerk_publishable_key"
  description = "Clerk publishable key (pk_test_* ou pk_live_*) consumida no build do Vite"
  type        = "SecureString"
  value       = var.clerk_publishable_key
  tags        = local.common_tags
}

resource "aws_ssm_parameter" "api_gateway_url" {
  name        = "${local.ssm_prefix}/api_gateway_url"
  description = "URL pública do Kong (esquema+host) — injetada no bundle como VITE_KONG_BASE_URL"
  type        = "String"
  value       = local.api_gateway_url
  tags        = local.common_tags
}

# ID da distribuição CloudFront — lido pelo workflow frontend-deploy
# para criar invalidations sem depender de filtro por Comment string.
resource "aws_ssm_parameter" "cloudfront_distribution_id" {
  name        = "${local.ssm_prefix}/cloudfront_distribution_id"
  description = "ID da distribuição CloudFront — consumido pelo workflow frontend-deploy"
  type        = "String"
  value       = aws_cloudfront_distribution.frontend.id
  tags        = local.common_tags
}
