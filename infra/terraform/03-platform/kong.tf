# ── Kong Ingress Controller ────────────────────────────────────────────
# Ponto de entrada público da API do ArchLens (modo DB-less, declarativo).
# Plugins globais (rate-limiting, CORS, key-auth) são aplicados via
# manifests K8s em infra/k8s/ingress/kong-config.yaml.
resource "helm_release" "kong" {
  name       = "kong"
  repository = "https://charts.konghq.com"
  chart      = "ingress"
  version    = var.kong_chart_version
  namespace  = data.kubernetes_namespace.archlens.metadata[0].name

  set = [
    # Proxy exposto externamente — endpoint público da API
    { name = "gateway.proxy.type", value = "LoadBalancer" },
    { name = "gateway.proxy.annotations.service\\.beta\\.kubernetes\\.io/aws-load-balancer-scheme", value = "internet-facing" },

    # Admin API — interno apenas (ClusterIP)
    { name = "gateway.admin.type", value = "ClusterIP" },
    { name = "gateway.admin.enabled", value = "true" },

    # Resources do proxy
    { name = "gateway.resources.requests.memory", value = "256Mi" },
    { name = "gateway.resources.requests.cpu", value = "250m" },
    { name = "gateway.resources.limits.memory", value = "512Mi" },
    { name = "gateway.resources.limits.cpu", value = "500m" },

    # Resources do controller
    { name = "controller.resources.requests.memory", value = "128Mi" },
    { name = "controller.resources.requests.cpu", value = "100m" },
    { name = "controller.resources.limits.memory", value = "256Mi" },
    { name = "controller.resources.limits.cpu", value = "250m" },
  ]

  depends_on = [
    data.kubernetes_namespace.archlens,
    helm_release.vault
  ]
}

# ── Data source para hostname público do Kong ────────────────────────
# O nome do service pode variar conforme a versão do chart.
# Verificar com: kubectl get svc -n archlens | grep kong
data "kubernetes_service" "kong" {
  metadata {
    name      = "kong-gateway-proxy"
    namespace = data.kubernetes_namespace.archlens.metadata[0].name
  }
  depends_on = [helm_release.kong]
}
