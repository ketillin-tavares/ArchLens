# ══════════════════════════════════════════════════════════════════════
#  LiteLLM Proxy — espelha o docker-compose
# ══════════════════════════════════════════════════════════════════════
#  Provider:    Gemini (3.1 Flash Lite Preview + 2.5 Flash fallback)
#  Guardrails:  Prompt Injection (callback) + Presidio PII + JSON validator
#  Cache:       in-memory, TTL 1h
#  DB:          litellm_db no RDS (STORE_MODEL_IN_DB=True)
#  Presidio:    sidecars analyzer + anonymizer (HTTP 3000)
# ══════════════════════════════════════════════════════════════════════

# ── LiteLLM Config (espelha gateways/litellm/litellm_config.yaml) ────
resource "kubernetes_config_map" "litellm" {
  metadata {
    name      = "litellm-config"
    namespace = data.kubernetes_namespace.archlens.metadata[0].name
  }

  data = {
    "config.yaml" = yamlencode({
      model_list = [
        {
          model_name = "archlens-vision"
          litellm_params = {
            model       = "gemini/gemini-3.1-flash-lite-preview"
            api_key     = "os.environ/GEMINI_API_KEY"
            max_tokens  = 4096
            temperature = 0.1
            timeout     = 120
            num_retries = 1
          }
          model_info = {
            description = "Gemini 3.1 Flash Lite Preview — vision — Google API"
          }
        },
        {
          model_name = "archlens-vision-fallback"
          litellm_params = {
            model       = "gemini/gemini-2.5-flash"
            api_key     = "os.environ/GEMINI_API_KEY"
            max_tokens  = 4096
            temperature = 0.1
            timeout     = 60
            num_retries = 2
          }
          model_info = {
            description = "Gemini 2.5 Flash — fallback vision"
          }
        },
        {
          model_name = "archlens-analyzer"
          litellm_params = {
            model       = "gemini/gemini-3.1-flash-lite-preview"
            api_key     = "os.environ/GEMINI_API_KEY"
            max_tokens  = 4096
            temperature = 0.1
            timeout     = 120
            num_retries = 1
          }
          model_info = {
            description = "Gemini 3.1 Flash Lite Preview — text-only — Google API"
          }
        },
        {
          model_name = "archlens-analyzer-fallback"
          litellm_params = {
            model       = "gemini/gemini-2.5-flash"
            api_key     = "os.environ/GEMINI_API_KEY"
            max_tokens  = 4096
            temperature = 0.1
            timeout     = 60
            num_retries = 2
          }
          model_info = {
            description = "Gemini 2.5 Flash — fallback text-only"
          }
        }
      ]

      litellm_settings = {
        callbacks = ["detect_prompt_injection"]
        prompt_injection_params = {
          heuristics_check = true
          similarity_check = true
          llm_api_check    = false
        }

        cache = true
        cache_params = {
          type                 = "local"
          ttl                  = 3600
          supported_call_types = ["acompletion", "completion"]
        }

        drop_params     = true
        set_verbose     = false
        request_timeout = 120
        num_retries     = 1
        retry_after     = 3
        allowed_fails   = 3
        cooldown_time   = 30

        context_window_fallbacks = [
          { "archlens-vision" = ["archlens-vision-fallback"] },
          { "archlens-analyzer" = ["archlens-analyzer-fallback"] }
        ]
        content_policy_fallbacks = [
          { "archlens-vision" = ["archlens-vision-fallback"] },
          { "archlens-analyzer" = ["archlens-analyzer-fallback"] }
        ]
      }

      guardrails = [
        {
          guardrail_name = "pii-masking"
          litellm_params = {
            guardrail                   = "presidio"
            mode                        = "pre_call"
            output_parse_pii            = true
            presidio_ad_hoc_recognizers = null
            presidio_language           = "pt"
            pii_entities_config = {
              EMAIL_ADDRESS = "MASK"
              PHONE_NUMBER  = "MASK"
              IP_ADDRESS    = "MASK"
              CREDIT_CARD   = "MASK"
              PERSON        = "MASK"
            }
          }
        },
        {
          guardrail_name = "json-validator"
          litellm_params = {
            guardrail = "guardrails.json_validator.JsonResponseValidator"
            mode      = "post_call"
          }
        }
      ]

      general_settings = {
        master_key   = "os.environ/LITELLM_MASTER_KEY"
        database_url = "os.environ/LITELLM_DATABASE_URL"
        alerting     = []
      }

      router_settings = {
        routing_strategy       = "simple-shuffle"
        allowed_fails          = 3
        cooldown_time          = 30
        enable_pre_call_checks = true
        fallbacks = [
          { "archlens-vision" = ["archlens-vision-fallback"] },
          { "archlens-analyzer" = ["archlens-analyzer-fallback"] }
        ]
      }
    })
  }
}

# ── Guardrails (codigo Python customizado) ───────────────────────────
# Montado como volume em /app/guardrails — espelha gateways/litellm/guardrails.
resource "kubernetes_config_map" "litellm_guardrails" {
  metadata {
    name      = "litellm-guardrails"
    namespace = data.kubernetes_namespace.archlens.metadata[0].name
  }

  data = {
    "__init__.py"       = file("${path.module}/../../../gateways/litellm/guardrails/__init__.py")
    "json_validator.py" = file("${path.module}/../../../gateways/litellm/guardrails/json_validator.py")
  }
}

# ── Bootstrap do litellm_db no RDS ────────────────────────────────────
# Job one-shot: cria database e usuario dedicados pra LiteLLM.
# Idempotente — seguro rodar varias vezes. Equivalente ao init-multiple-dbs.sh
# do compose (cria o mesmo litellm_db + litellm_user).
resource "kubernetes_job" "litellm_db_bootstrap" {
  metadata {
    name      = "litellm-db-bootstrap"
    namespace = data.kubernetes_namespace.archlens.metadata[0].name
  }

  spec {
    backoff_limit = 3

    template {
      metadata {
        labels = { app = "litellm-db-bootstrap" }
      }

      spec {
        restart_policy = "OnFailure"

        container {
          name  = "psql"
          image = "postgres:16-alpine"

          env {
            name  = "PGHOST"
            value = local.rds_address
          }
          env {
            name  = "PGPORT"
            value = "5432"
          }
          env {
            name  = "PGUSER"
            value = "archlens"
          }
          env {
            name  = "PGPASSWORD"
            value = var.db_password
          }
          # RDS instance está configurado com rds.force_ssl=1; conexões plain TCP são rejeitadas
          env {
            name  = "PGSSLMODE"
            value = "require"
          }
          env {
            name  = "LITELLM_DB_USER"
            value = "litellm_user"
          }
          env {
            name  = "LITELLM_DB_PASS"
            value = var.litellm_db_password
          }

          command = ["/bin/sh", "-c"]
          args = [
            <<-SH
              set -e
              psql -d postgres -tc "SELECT 1 FROM pg_roles WHERE rolname='$LITELLM_DB_USER'" | grep -q 1 || \
                psql -d postgres -c "CREATE USER $LITELLM_DB_USER WITH PASSWORD '$LITELLM_DB_PASS';"
              psql -d postgres -c "GRANT $LITELLM_DB_USER TO CURRENT_USER;"
              psql -d postgres -tc "SELECT 1 FROM pg_database WHERE datname='litellm_db'" | grep -q 1 || \
                psql -d postgres -c "CREATE DATABASE litellm_db OWNER $LITELLM_DB_USER;"
              psql -d postgres -c "GRANT ALL PRIVILEGES ON DATABASE litellm_db TO $LITELLM_DB_USER;"
            SH
          ]
        }
      }
    }

    completions = 1
  }

  wait_for_completion = true

  timeouts {
    create = "5m"
    update = "5m"
  }
}

# ── Presidio Analyzer (sidecar service) ──────────────────────────────
resource "kubernetes_deployment" "presidio_analyzer" {
  metadata {
    name      = "presidio-analyzer"
    namespace = data.kubernetes_namespace.archlens.metadata[0].name
    labels    = { app = "presidio-analyzer" }
  }

  spec {
    replicas = 1
    selector { match_labels = { app = "presidio-analyzer" } }

    template {
      metadata { labels = { app = "presidio-analyzer" } }

      spec {
        container {
          name  = "presidio-analyzer"
          image = "mcr.microsoft.com/presidio-analyzer:latest"

          port {
            container_port = 3000
            name           = "http"
          }

          resources {
            requests = {
              memory = "256Mi"
              cpu    = "100m"
            }
            limits = {
              memory = "512Mi"
              cpu    = "500m"
            }
          }

          liveness_probe {
            http_get {
              path = "/health"
              port = 3000
            }
            initial_delay_seconds = 60
            period_seconds        = 30
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "presidio_analyzer" {
  metadata {
    name      = "presidio-analyzer"
    namespace = data.kubernetes_namespace.archlens.metadata[0].name
    labels    = { app = "presidio-analyzer" }
  }

  spec {
    selector = { app = "presidio-analyzer" }
    type     = "ClusterIP"

    port {
      name        = "http"
      port        = 3000
      target_port = 3000
      protocol    = "TCP"
    }
  }
}

# ── Presidio Anonymizer (sidecar service) ────────────────────────────
resource "kubernetes_deployment" "presidio_anonymizer" {
  metadata {
    name      = "presidio-anonymizer"
    namespace = data.kubernetes_namespace.archlens.metadata[0].name
    labels    = { app = "presidio-anonymizer" }
  }

  spec {
    replicas = 1
    selector { match_labels = { app = "presidio-anonymizer" } }

    template {
      metadata { labels = { app = "presidio-anonymizer" } }

      spec {
        container {
          name  = "presidio-anonymizer"
          image = "mcr.microsoft.com/presidio-anonymizer:latest"

          port {
            container_port = 3000
            name           = "http"
          }

          resources {
            requests = {
              memory = "128Mi"
              cpu    = "100m"
            }
            limits = {
              memory = "256Mi"
              cpu    = "250m"
            }
          }

          liveness_probe {
            http_get {
              path = "/health"
              port = 3000
            }
            initial_delay_seconds = 30
            period_seconds        = 30
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "presidio_anonymizer" {
  metadata {
    name      = "presidio-anonymizer"
    namespace = data.kubernetes_namespace.archlens.metadata[0].name
    labels    = { app = "presidio-anonymizer" }
  }

  spec {
    selector = { app = "presidio-anonymizer" }
    type     = "ClusterIP"

    port {
      name        = "http"
      port        = 3000
      target_port = 3000
      protocol    = "TCP"
    }
  }
}

# ── LiteLLM Deployment ─────────────────────────────────────────────────
resource "kubernetes_deployment" "litellm" {
  metadata {
    name      = "litellm-proxy"
    namespace = data.kubernetes_namespace.archlens.metadata[0].name
    labels = {
      app     = "litellm-proxy"
      project = "archlens"
    }
  }

  spec {
    replicas = 1

    selector {
      match_labels = { app = "litellm-proxy" }
    }

    template {
      metadata {
        labels = { app = "litellm-proxy" }
        annotations = {
          # Vault Agent Injector — injeta secrets como arquivo /vault/secrets/litellm
          "vault.hashicorp.com/agent-inject"                  = "true"
          "vault.hashicorp.com/role"                          = "archlens-services"
          "vault.hashicorp.com/agent-inject-secret-litellm"   = "secret/data/archlens/litellm"
          "vault.hashicorp.com/agent-inject-template-litellm" = <<-TMPL
            {{- with secret "secret/data/archlens/litellm" -}}
            export GEMINI_API_KEY="{{ .Data.data.GEMINI_API_KEY }}"
            export LITELLM_MASTER_KEY="{{ .Data.data.MASTER_KEY }}"
            {{- end }}
          TMPL
        }
      }

      spec {
        service_account_name = "default"

        container {
          name  = "litellm-proxy"
          image = var.litellm_image

          security_context {
            run_as_non_root            = true
            run_as_user                = 1000
            read_only_root_filesystem  = false
            allow_privilege_escalation = false
          }

          # Instalar guardrails Python deps em runtime (presidio) e carregar
          # secrets do Vault. O base image nao tem esses pacotes — equivalente
          # ao pip install do Dockerfile custom em gateways/litellm/Dockerfile.
          command = ["/bin/sh", "-c"]
          args = [
            <<-CMD
              pip install --no-cache-dir presidio-analyzer presidio-anonymizer && \
              { [ -f /vault/secrets/litellm ] && . /vault/secrets/litellm; } ; \
              litellm --config /app/config.yaml --host 0.0.0.0 --port 4000
            CMD
          ]

          env {
            name  = "HOME"
            value = "/tmp"
          }
          env {
            name  = "LITELLM_DATABASE_URL"
            value = "postgresql://litellm_user:${var.litellm_db_password}@${local.rds_address}:5432/litellm_db"
          }
          env {
            name  = "STORE_MODEL_IN_DB"
            value = "True"
          }
          env {
            name  = "PRESIDIO_ANALYZER_API_BASE"
            value = "http://presidio-analyzer.archlens.svc.cluster.local:3000"
          }
          env {
            name  = "PRESIDIO_ANONYMIZER_API_BASE"
            value = "http://presidio-anonymizer.archlens.svc.cluster.local:3000"
          }

          port {
            container_port = 4000
            name           = "http"
          }

          volume_mount {
            name       = "litellm-config"
            mount_path = "/app/config.yaml"
            sub_path   = "config.yaml"
            read_only  = true
          }

          volume_mount {
            name       = "litellm-guardrails"
            mount_path = "/app/guardrails"
            read_only  = true
          }

          resources {
            requests = {
              memory = "512Mi"
              cpu    = "250m"
            }
            limits = {
              memory = "1536Mi"
              cpu    = "500m"
            }
          }

          liveness_probe {
            http_get {
              path = "/health/liveliness"
              port = 4000
            }
            initial_delay_seconds = 90
            period_seconds        = 10
            failure_threshold     = 3
          }

          readiness_probe {
            http_get {
              path = "/health/readiness"
              port = 4000
            }
            initial_delay_seconds = 60
            period_seconds        = 5
          }
        }

        volume {
          name = "litellm-config"
          config_map {
            name = kubernetes_config_map.litellm.metadata[0].name
          }
        }

        volume {
          name = "litellm-guardrails"
          config_map {
            name = kubernetes_config_map.litellm_guardrails.metadata[0].name
          }
        }
      }
    }
  }

  depends_on = [
    data.kubernetes_namespace.archlens,
    helm_release.vault,
    kubernetes_config_map.litellm,
    kubernetes_config_map.litellm_guardrails,
    kubernetes_job.litellm_db_bootstrap,
    kubernetes_service.presidio_analyzer,
    kubernetes_service.presidio_anonymizer
  ]
}

# ── LiteLLM Service ───────────────────────────────────────────────────
resource "kubernetes_service" "litellm" {
  metadata {
    name      = "litellm-proxy"
    namespace = data.kubernetes_namespace.archlens.metadata[0].name
    labels    = { app = "litellm-proxy" }
  }

  spec {
    selector = { app = "litellm-proxy" }
    type     = "ClusterIP"

    port {
      name        = "http"
      port        = 4000
      target_port = 4000
      protocol    = "TCP"
    }
  }
}
