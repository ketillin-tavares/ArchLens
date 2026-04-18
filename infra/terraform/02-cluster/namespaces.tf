# ── Namespace archlens ────────────────────────────────────────────────
resource "kubernetes_namespace" "archlens" {
  metadata {
    name = "archlens"
    labels = {
      project     = "archlens"
      environment = var.environment
    }
  }

  depends_on = [module.eks]
}

# ── Service Accounts dos Microserviços (IRSA) ────────────────────────
# Cada SA é anotado com o ARN do IAM role criado no workspace 01-foundation,
# permitindo que os pods acessem recursos AWS sem chaves hardcoded.

resource "kubernetes_service_account" "upload_service" {
  metadata {
    name      = "upload-service-sa"
    namespace = kubernetes_namespace.archlens.metadata[0].name

    annotations = {
      "eks.amazonaws.com/role-arn" = data.terraform_remote_state.foundation.outputs.upload_service_role_arn
    }
  }
}

resource "kubernetes_service_account" "processing_service" {
  metadata {
    name      = "processing-service-sa"
    namespace = kubernetes_namespace.archlens.metadata[0].name

    annotations = {
      "eks.amazonaws.com/role-arn" = data.terraform_remote_state.foundation.outputs.processing_service_role_arn
    }
  }
}
