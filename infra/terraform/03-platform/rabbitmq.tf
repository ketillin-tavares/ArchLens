# ── RabbitMQ ──────────────────────────────────────────────────────────
# Backbone de mensageria do ArchLens (Bitnami Helm chart).
# Exchange topic "analise.events" com filas e bindings pré-configurados
# via definitions JSON carregado automaticamente na inicialização.
resource "helm_release" "rabbitmq" {
  name       = "rabbitmq"
  repository = "https://charts.bitnami.com/bitnami"
  chart      = "rabbitmq"
  version    = var.rabbitmq_chart_version
  namespace  = data.kubernetes_namespace.archlens.metadata[0].name

  # Credenciais
  set {
    name  = "auth.username"
    value = "archlens"
  }
  set_sensitive {
    name  = "auth.password"
    value = var.rabbitmq_password
  }
  set_sensitive {
    name  = "auth.erlangCookie"
    value = var.rabbitmq_erlang_cookie
  }

  # Persistência
  set {
    name  = "persistence.enabled"
    value = "true"
  }
  set {
    name  = "persistence.size"
    value = var.rabbitmq_storage_size
  }
  set {
    name  = "persistence.storageClass"
    value = "gp2"
  }

  # Resources
  set {
    name  = "resources.requests.memory"
    value = "256Mi"
  }
  set {
    name  = "resources.requests.cpu"
    value = "100m"
  }
  set {
    name  = "resources.limits.memory"
    value = "512Mi"
  }
  set {
    name  = "resources.limits.cpu"
    value = "500m"
  }

  # Management Plugin (UI na porta 15672) + peer discovery K8s
  set {
    name  = "plugins"
    value = "rabbitmq_management rabbitmq_peer_discovery_k8s"
  }
  set {
    name  = "service.type"
    value = "ClusterIP"
  }

  # Replication: 1 node (economizar para hackathon)
  set {
    name  = "replicaCount"
    value = "1"
  }

  # Definitions — carrega exchange, filas e bindings automaticamente
  set {
    name  = "loadDefinition.enabled"
    value = "true"
  }
  set {
    name  = "loadDefinition.existingSecret"
    value = kubernetes_secret.rabbitmq_definitions.metadata[0].name
  }

  depends_on = [
    data.kubernetes_namespace.archlens,
    kubernetes_secret.rabbitmq_definitions
  ]
}

# ── RabbitMQ Definitions (exchange + filas + bindings) ────────────────
# Carregado automaticamente pelo chart Bitnami via loadDefinition.
resource "kubernetes_secret" "rabbitmq_definitions" {
  metadata {
    name      = "rabbitmq-definitions"
    namespace = data.kubernetes_namespace.archlens.metadata[0].name
  }

  data = {
    "load_definition.json" = jsonencode({
      rabbit_version = "3.12"
      # Usuario "archlens" e criado pelo chart Bitnami via auth.username/auth.password.
      # Nao declarar aqui para evitar sobrescrever com password_hash vazio.
      vhosts = [{ name = "/" }]
      exchanges = [
        {
          name        = "analise.events"
          vhost       = "/"
          type        = "topic"
          durable     = true
          auto_delete = false
          arguments   = {}
        },
        {
          name        = "analise.dlx"
          vhost       = "/"
          type        = "direct"
          durable     = true
          auto_delete = false
          arguments   = {}
        }
      ]
      queues = [
        {
          name        = "analise.processamento.queue"
          vhost       = "/"
          durable     = true
          auto_delete = false
          arguments = {
            "x-dead-letter-exchange"    = "analise.dlx"
            "x-dead-letter-routing-key" = "analise.processamento.dead"
          }
        },
        {
          name        = "analise.relatorio.queue"
          vhost       = "/"
          durable     = true
          auto_delete = false
          arguments = {
            "x-dead-letter-exchange"    = "analise.dlx"
            "x-dead-letter-routing-key" = "analise.relatorio.dead"
          }
        },
        {
          name        = "analise.status.queue"
          vhost       = "/"
          durable     = true
          auto_delete = false
          arguments = {
            "x-dead-letter-exchange"    = "analise.dlx"
            "x-dead-letter-routing-key" = "analise.status.dead"
          }
        },
        {
          name        = "analise.dlq"
          vhost       = "/"
          durable     = true
          auto_delete = false
          arguments   = {}
        }
      ]
      bindings = [
        {
          source           = "analise.events"
          vhost            = "/"
          destination      = "analise.processamento.queue"
          destination_type = "queue"
          routing_key      = "analise.diagrama.enviado"
          arguments        = {}
        },
        {
          source           = "analise.events"
          vhost            = "/"
          destination      = "analise.relatorio.queue"
          destination_type = "queue"
          routing_key      = "analise.processamento.concluida"
          arguments        = {}
        },
        {
          source           = "analise.events"
          vhost            = "/"
          destination      = "analise.status.queue"
          destination_type = "queue"
          routing_key      = "analise.processamento.iniciado"
          arguments        = {}
        },
        {
          source           = "analise.events"
          vhost            = "/"
          destination      = "analise.status.queue"
          destination_type = "queue"
          routing_key      = "analise.processamento.concluida"
          arguments        = {}
        },
        {
          source           = "analise.events"
          vhost            = "/"
          destination      = "analise.status.queue"
          destination_type = "queue"
          routing_key      = "analise.processamento.falhou"
          arguments        = {}
        },
        {
          source           = "analise.events"
          vhost            = "/"
          destination      = "analise.status.queue"
          destination_type = "queue"
          routing_key      = "analise.relatorio.gerado"
          arguments        = {}
        }
      ]
    })
  }

  depends_on = [data.kubernetes_namespace.archlens]
}
