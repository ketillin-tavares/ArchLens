# ── RabbitMQ ──────────────────────────────────────────────────────────
# Backbone de mensageria do ArchLens (Bitnami Helm chart).
# Exchange topic "analise.events" com filas e bindings pré-configurados
# via definitions JSON carregado automaticamente na inicialização.
resource "helm_release" "rabbitmq" {
  name      = "rabbitmq"
  chart     = "${path.module}/charts/rabbitmq"
  version   = var.rabbitmq_chart_version
  namespace = data.kubernetes_namespace.archlens.metadata[0].name

  set = [
    # Override para registry legacy do Bitnami — desde Aug/2025 a catalog padrão
    # do Bitnami exige assinatura paga. As mesmas imagens públicas migraram para
    # bitnamilegacy/* (não são inseguras, só fora do catálogo "secure" pago).
    # Docs: https://github.com/bitnami/charts/issues/35164
    { name = "global.security.allowInsecureImages", value = "true" },
    { name = "image.registry", value = "docker.io" },
    { name = "image.repository", value = "bitnamilegacy/rabbitmq" },

    # Credenciais (usuário)
    { name = "auth.username", value = "archlens" },

    # Persistência
    { name = "persistence.enabled", value = "true" },
    { name = "persistence.size", value = var.rabbitmq_storage_size },
    { name = "persistence.storageClass", value = "gp2" },

    # Resources
    { name = "resources.requests.memory", value = "256Mi" },
    { name = "resources.requests.cpu", value = "100m" },
    { name = "resources.limits.memory", value = "512Mi" },
    { name = "resources.limits.cpu", value = "500m" },

    # Management Plugin (UI na porta 15672) + peer discovery K8s
    { name = "plugins", value = "rabbitmq_management rabbitmq_peer_discovery_k8s" },
    { name = "service.type", value = "ClusterIP" },

    # Replication: 1 node (economizar para hackathon)
    { name = "replicaCount", value = "1" },

    # Definitions — carrega exchange, filas e bindings automaticamente
    { name = "loadDefinition.enabled", value = "true" },
    { name = "loadDefinition.existingSecret", value = kubernetes_secret.rabbitmq_definitions.metadata[0].name },
  ]

  set_sensitive = [
    { name = "auth.password", value = var.rabbitmq_password },
    { name = "auth.erlangCookie", value = var.rabbitmq_erlang_cookie },
  ]

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
      # Permissoes do user archlens no vhost /. Sem isto o chart nao concede
      # permissao automatica e o broker fecha conexoes apos auth (Connection.Close).
      permissions = [
        {
          user      = "archlens"
          vhost     = "/"
          configure = ".*"
          write     = ".*"
          read      = ".*"
        }
      ]
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
