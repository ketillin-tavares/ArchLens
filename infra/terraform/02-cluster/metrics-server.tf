# ── Metrics Server ────────────────────────────────────────────────────
# Pré-requisito para HPA (Horizontal Pod Autoscaler).
# Coleta métricas de CPU e memória dos pods via Kubelet API.
# Sem o metrics-server, o controller do HPA não consegue escalar.
resource "helm_release" "metrics_server" {
  name      = "metrics-server"
  chart     = "${path.module}/charts/metrics-server"
  version   = var.metrics_server_chart_version
  namespace = "kube-system"

  set = [
    { name = "replicas", value = "1" },
    { name = "resources.requests.cpu", value = "100m" },
    { name = "resources.requests.memory", value = "128Mi" },
    { name = "resources.limits.cpu", value = "250m" },
    { name = "resources.limits.memory", value = "256Mi" },
  ]

  depends_on = [module.eks]
}
