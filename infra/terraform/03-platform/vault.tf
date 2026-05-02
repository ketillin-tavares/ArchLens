# ── Vault ─────────────────────────────────────────────────────────────
# HashiCorp Vault em modo standalone (persistente, requer init + unseal manual).
# O Vault Agent Injector fica ativo para injetar secrets nos pods via anotações.
resource "helm_release" "vault" {
  name      = "vault"
  chart     = "${path.module}/charts/vault"
  version   = var.vault_chart_version
  namespace = data.kubernetes_namespace.archlens.metadata[0].name

  set = [
    # Standalone mode: persistente, requer init + unseal manual
    { name = "server.dev.enabled", value = "false" },
    { name = "server.standalone.enabled", value = "true" },
    { name = "server.ha.enabled", value = "false" },

    # Storage persistente (usa aws-ebs-csi-driver instalado no workspace 02-cluster)
    { name = "server.dataStorage.enabled", value = "true" },
    { name = "server.dataStorage.size", value = var.vault_storage_size },
    { name = "server.dataStorage.storageClass", value = var.vault_storage_class },

    # Vault Agent Injector — injeta secrets nos pods via anotações
    { name = "injector.enabled", value = "true" },
    { name = "injector.replicas", value = "1" },

    # Resources do Injector — essencial para evitar OOMKill sob pressao
    # (ele fica no caminho de admission de TODO pod do namespace).
    { name = "injector.resources.requests.memory", value = "64Mi" },
    { name = "injector.resources.requests.cpu", value = "50m" },
    { name = "injector.resources.limits.memory", value = "128Mi" },
    { name = "injector.resources.limits.cpu", value = "250m" },

    # Resources dos Vault Agents (initContainer + sidecar) injetados em CADA pod
    # que usa `vault.hashicorp.com/agent-inject: "true"`. Sem isso, cada pod
    # extra adiciona quantidade de memoria/CPU desconhecida.
    { name = "injector.agentDefaults.cpuRequest", value = "50m" },
    { name = "injector.agentDefaults.memRequest", value = "64Mi" },
    { name = "injector.agentDefaults.cpuLimit", value = "100m" },
    { name = "injector.agentDefaults.memLimit", value = "128Mi" },

    # Service type para acesso ao Vault
    # LoadBalancer: para bootstrap inicial (init + unseal + popular secrets)
    # ClusterIP: após bootstrap, restringir acesso externo
    { name = "server.service.type", value = var.vault_service_type },
    { name = "server.service.annotations.service\\.beta\\.kubernetes\\.io/aws-load-balancer-scheme", value = "internet-facing" },

    # UI habilitada para gestão de secrets
    { name = "ui.enabled", value = "true" },
    { name = "ui.serviceType", value = "ClusterIP" },

    # Resources
    { name = "server.resources.requests.memory", value = "256Mi" },
    { name = "server.resources.requests.cpu", value = "250m" },
    { name = "server.resources.limits.memory", value = "512Mi" },
    { name = "server.resources.limits.cpu", value = "500m" },
  ]

  depends_on = [data.kubernetes_namespace.archlens]
}

# ── Data source para hostname do LoadBalancer ────────────────────────
# Só resolve quando server.service.type = "LoadBalancer"
data "kubernetes_service" "vault" {
  metadata {
    name      = "vault"
    namespace = data.kubernetes_namespace.archlens.metadata[0].name
  }
  depends_on = [helm_release.vault]
}
