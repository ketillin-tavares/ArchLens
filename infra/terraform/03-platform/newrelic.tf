# ── New Relic — Namespace separado ────────────────────────────────────
# Namespace dedicado para componentes de observabilidade do New Relic.
# Separar do namespace archlens evita conflitos e facilita cleanup.
resource "kubernetes_namespace" "newrelic" {
  metadata {
    name = "newrelic"
    labels = {
      project     = "archlens"
      environment = var.environment
    }
  }
}

# ── New Relic Bundle (Infrastructure + K8s Integration) ──────────────
# Chart oficial nri-bundle: instala Infrastructure Agent (DaemonSet),
# kube-state-metrics, events, metadata injection, logging e Prometheus.
# Docs: https://github.com/newrelic/helm-charts/tree/master/charts/nri-bundle
resource "helm_release" "newrelic" {
  name       = "newrelic-bundle"
  repository = "https://helm-charts.newrelic.com"
  chart      = "nri-bundle"
  version    = var.newrelic_chart_version
  namespace  = kubernetes_namespace.newrelic.metadata[0].name

  # Global — cluster e privileged
  set = [
    { name = "global.cluster", value = local.cluster_name },
    { name = "global.privileged", value = "true" },

    # Infrastructure Agent (DaemonSet — roda em TODOS os nodes)
    { name = "newrelic-infrastructure.enabled", value = "true" },

    # Kubernetes Events Integration
    { name = "nri-kube-events.enabled", value = "true" },

    # Kubernetes State Metrics (pods, deployments, HPA, PVC)
    { name = "kube-state-metrics.enabled", value = "true" },

    # Metadata Injection — correlaciona APM traces com pods/nodes no NR UI
    { name = "nri-metadata-injection.enabled", value = "true" },

    # Prometheus Agent — scrape métricas internas dos pods
    { name = "newrelic-prometheus-agent.enabled", value = "true" },
    { name = "newrelic-prometheus-agent.config.kubernetes.integrations_filter.enabled", value = "false" },

    # Logs — encaminha logs de todos os containers para New Relic Logs
    { name = "newrelic-logging.enabled", value = "true" },
  ]

  # License key (sensível)
  set_sensitive = [
    { name = "global.licenseKey", value = var.newrelic_license_key },
  ]

  depends_on = [kubernetes_namespace.newrelic]
}

# ── Integração RDS PostgreSQL ────────────────────────────────────────
# O nri-postgresql coleta métricas do RDS: conexões, queries, IOPS, locks.
# Conecta via rede privada (SG do RDS permite acesso dos nodes EKS).
resource "kubernetes_config_map" "newrelic_rds_integration" {
  metadata {
    name      = "nri-postgresql-config"
    namespace = kubernetes_namespace.newrelic.metadata[0].name
  }

  data = {
    "postgresql-config.yml" = <<-YAML
      integrations:
        - name: nri-postgresql
          env:
            HOSTNAME: ${local.rds_address}
            PORT: "5432"
            USERNAME: archlens
            PASSWORD: $${NRI_POSTGRESQL_PASSWORD}
            DATABASE: archlens
            COLLECT_DB_LOCK_METRICS: "true"
            COLLECT_BLOAT_METRICS: "false"
            CUSTOM_METRICS_QUERY: >
              SELECT
                datname AS "database",
                numbackends AS "connections",
                xact_commit AS "transactions_committed",
                xact_rollback AS "transactions_rolled_back",
                blks_read AS "blocks_read",
                blks_hit AS "blocks_hit",
                tup_returned AS "tuples_returned",
                tup_fetched AS "tuples_fetched",
                tup_inserted AS "tuples_inserted",
                tup_updated AS "tuples_updated",
                tup_deleted AS "tuples_deleted"
              FROM pg_stat_database
              WHERE datname NOT IN ('postgres', 'template0', 'template1')
          interval: 30s
          labels:
            env: ${var.environment}
            role: database
            project: archlens
    YAML
  }
}

resource "kubernetes_secret" "newrelic_rds_creds" {
  metadata {
    name      = "nri-postgresql-creds"
    namespace = kubernetes_namespace.newrelic.metadata[0].name
  }

  data = {
    NRI_POSTGRESQL_PASSWORD = var.db_password
  }
}

# ── Integração RabbitMQ ──────────────────────────────────────────────
# O nri-rabbitmq coleta métricas via Management API (porta 15672):
# filas, mensagens, consumers, exchanges.
resource "kubernetes_config_map" "newrelic_rabbitmq_integration" {
  metadata {
    name      = "nri-rabbitmq-config"
    namespace = kubernetes_namespace.newrelic.metadata[0].name
  }

  data = {
    "rabbitmq-config.yml" = <<-YAML
      integrations:
        - name: nri-rabbitmq
          env:
            HOSTNAME: rabbitmq.archlens.svc.cluster.local
            PORT: "15672"
            USERNAME: archlens
            PASSWORD: $${NRI_RABBITMQ_PASSWORD}
            USE_SSL: "false"
            QUEUES_REGEXES: '["analise\\..*"]'
            EXCHANGES_REGEXES: '["analise\\..*"]'
          interval: 30s
          labels:
            env: ${var.environment}
            role: messaging
            project: archlens
    YAML
  }
}

resource "kubernetes_secret" "newrelic_rabbitmq_creds" {
  metadata {
    name      = "nri-rabbitmq-creds"
    namespace = kubernetes_namespace.newrelic.metadata[0].name
  }

  data = {
    NRI_RABBITMQ_PASSWORD = var.rabbitmq_password
  }
}

# ── Configs customizadas de integracoes (PostgreSQL + RabbitMQ) ──────
# ConfigMap com nome unico para evitar conflito com o recurso criado pelo
# chart nri-bundle ("newrelic-bundle-nrk8s-integrations-cfg"). Deve ser
# montado como volume adicional no Infrastructure Agent via values do chart.
resource "kubernetes_config_map" "newrelic_integrations_cfg" {
  metadata {
    name      = "nri-custom-integrations"
    namespace = kubernetes_namespace.newrelic.metadata[0].name
  }

  data = {
    "postgresql-config.yml" = kubernetes_config_map.newrelic_rds_integration.data["postgresql-config.yml"]
    "rabbitmq-config.yml"   = kubernetes_config_map.newrelic_rabbitmq_integration.data["rabbitmq-config.yml"]
  }

  depends_on = [helm_release.newrelic]
}
