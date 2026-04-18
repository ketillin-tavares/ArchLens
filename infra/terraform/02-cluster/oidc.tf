# ── OIDC Provider ─────────────────────────────────────────────────────
# Necessário para IRSA (IAM Roles for Service Accounts).
# Permite que pods assumam IAM roles via Service Account annotations.
data "tls_certificate" "eks_oidc" {
  url = module.eks.cluster_oidc_issuer_url
}

resource "aws_iam_openid_connect_provider" "eks" {
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.eks_oidc.certificates[0].sha1_fingerprint]
  url             = module.eks.cluster_oidc_issuer_url

  tags = local.common_tags
}
