# ── Vault ─────────────────────────────────────────────────────────────
# HashiCorp Vault em modo standalone (persistente, requer init + unseal manual).
# O Vault Agent Injector fica ativo para injetar secrets nos pods via anotações.
resource "helm_release" "vault" {
  name       = "vault"
  repository = "https://helm.releases.hashicorp.com"
  chart      = "vault"
  version    = var.vault_chart_version
  namespace  = data.kubernetes_namespace.archlens.metadata[0].name

  # Standalone mode: persistente, requer init + unseal manual
  set {
    name  = "server.dev.enabled"
    value = "false"
  }
  set {
    name  = "server.standalone.enabled"
    value = "true"
  }
  set {
    name  = "server.ha.enabled"
    value = "false"
  }

  # Storage persistente (usa aws-ebs-csi-driver instalado no workspace 02-cluster)
  set {
    name  = "server.dataStorage.enabled"
    value = "true"
  }
  set {
    name  = "server.dataStorage.size"
    value = var.vault_storage_size
  }
  set {
    name  = "server.dataStorage.storageClass"
    value = var.vault_storage_class
  }

  # Vault Agent Injector — injeta secrets nos pods via anotações
  set {
    name  = "injector.enabled"
    value = "true"
  }
  set {
    name  = "injector.replicas"
    value = "1"
  }

  # Resources do Injector — essencial para evitar OOMKill sob pressao
  # (ele fica no caminho de admission de TODO pod do namespace).
  set {
    name  = "injector.resources.requests.memory"
    value = "64Mi"
  }
  set {
    name  = "injector.resources.requests.cpu"
    value = "50m"
  }
  set {
    name  = "injector.resources.limits.memory"
    value = "128Mi"
  }
  set {
    name  = "injector.resources.limits.cpu"
    value = "250m"
  }

  # Resources dos Vault Agents (initContainer + sidecar) injetados em CADA pod
  # que usa `vault.hashicorp.com/agent-inject: "true"`. Sem isso, cada pod
  # extra adiciona quantidade de memoria/CPU desconhecida.
  set {
    name  = "injector.agentDefaults.cpuRequest"
    value = "50m"
  }
  set {
    name  = "injector.agentDefaults.memRequest"
    value = "64Mi"
  }
  set {
    name  = "injector.agentDefaults.cpuLimit"
    value = "100m"
  }
  set {
    name  = "injector.agentDefaults.memLimit"
    value = "128Mi"
  }

  # Service type para acesso ao Vault
  # LoadBalancer: para bootstrap inicial (init + unseal + popular secrets)
  # ClusterIP: após bootstrap, restringir acesso externo
  set {
    name  = "server.service.type"
    value = var.vault_service_type
  }
  set {
    name  = "server.service.annotations.service\\.beta\\.kubernetes\\.io/aws-load-balancer-scheme"
    value = "internet-facing"
  }

  # UI habilitada para gestão de secrets
  set {
    name  = "ui.enabled"
    value = "true"
  }
  set {
    name  = "ui.serviceType"
    value = "ClusterIP"
  }

  # Resources
  set {
    name  = "server.resources.requests.memory"
    value = "256Mi"
  }
  set {
    name  = "server.resources.requests.cpu"
    value = "250m"
  }
  set {
    name  = "server.resources.limits.memory"
    value = "512Mi"
  }
  set {
    name  = "server.resources.limits.cpu"
    value = "500m"
  }

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
