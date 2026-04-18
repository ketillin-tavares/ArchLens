# ── Metrics Server ────────────────────────────────────────────────────
# Pré-requisito para HPA (Horizontal Pod Autoscaler).
# Coleta métricas de CPU e memória dos pods via Kubelet API.
# Sem o metrics-server, o controller do HPA não consegue escalar.
resource "helm_release" "metrics_server" {
  name       = "metrics-server"
  repository = "https://kubernetes-sigs.github.io/metrics-server/"
  chart      = "metrics-server"
  version    = var.metrics_server_chart_version
  namespace  = "kube-system"

  # Réplicas — 1 para dev, 2+ para produção
  set {
    name  = "replicas"
    value = "1"
  }

  # Resources mínimos
  set {
    name  = "resources.requests.cpu"
    value = "100m"
  }
  set {
    name  = "resources.requests.memory"
    value = "128Mi"
  }
  set {
    name  = "resources.limits.cpu"
    value = "250m"
  }
  set {
    name  = "resources.limits.memory"
    value = "256Mi"
  }

  depends_on = [module.eks]
}
