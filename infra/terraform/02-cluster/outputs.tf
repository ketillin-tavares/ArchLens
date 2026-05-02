# ── EKS ────────────────────────────────────────────────────────────────
output "cluster_name" {
  value       = module.eks.cluster_name
  description = "Nome do cluster EKS — usado por kubectl e pelo workspace 03-platform"
}

output "cluster_endpoint" {
  value       = module.eks.cluster_endpoint
  description = "URL do API server do EKS — necessário para configurar providers Kubernetes/Helm"
}

output "cluster_ca" {
  value       = module.eks.cluster_certificate_authority_data
  description = "Certificado CA do cluster em base64 — usado na autenticação kubectl"
}

# ── OIDC ───────────────────────────────────────────────────────────────
output "cluster_oidc_issuer_url" {
  value       = module.eks.cluster_oidc_issuer_url
  description = "URL do OIDC issuer do EKS — base para configuração IRSA"
}

output "oidc_provider_arn" {
  value       = module.eks.oidc_provider_arn
  description = "ARN do OIDC provider — referenciado nas trust policies dos IRSA roles"
}

# Extrair só o ID do OIDC (sem https://) para atualizar o workspace 01-foundation
output "oidc_provider_id" {
  value       = replace(module.eks.cluster_oidc_issuer_url, "https://", "")
  description = "OIDC provider ID sem prefixo https:// — usar para atualizar locals.oidc_provider no 01-foundation"
}
