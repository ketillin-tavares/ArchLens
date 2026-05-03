# ══════════════════════════════════════════════════════════════════════
#  Bootstrap dos databases dos 3 services no RDS
# ══════════════════════════════════════════════════════════════════════
#  Cria user dedicado e database para cada service. Idempotente.
#  Equivalente ao init-multiple-dbs.sh do docker-compose local
#  (services/*/init-multiple-dbs.sh ou similar).
#
#  Cada user usa a MESMA senha do master (var.db_password) — simplifica
#  o setup de Vault sem perder isolamento de databases.
#
#  Postgres 16+ exige `GRANT <user> TO CURRENT_USER` antes de
#  `CREATE DATABASE ... OWNER <user>` (mesma restrição do litellm bootstrap).
# ══════════════════════════════════════════════════════════════════════

locals {
  service_databases = {
    upload     = { user = "upload_user", db = "upload_db" }
    processing = { user = "processing_user", db = "processing_db" }
    report     = { user = "report_user", db = "report_db" }
  }
}

resource "kubernetes_job" "service_db_bootstrap" {
  for_each = local.service_databases

  metadata {
    name      = "${each.key}-db-bootstrap"
    namespace = data.kubernetes_namespace.archlens.metadata[0].name
  }

  spec {
    backoff_limit = 3

    template {
      metadata {
        labels = { app = "${each.key}-db-bootstrap" }
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
          env {
            name  = "PGSSLMODE"
            value = "require"
          }
          env {
            name  = "TARGET_USER"
            value = each.value.user
          }
          env {
            name  = "TARGET_PASS"
            value = var.db_password
          }
          env {
            name  = "TARGET_DB"
            value = each.value.db
          }

          command = ["/bin/sh", "-c"]
          args = [
            <<-SH
              set -e
              psql -d postgres -tc "SELECT 1 FROM pg_roles WHERE rolname='$TARGET_USER'" | grep -q 1 || \
                psql -d postgres -c "CREATE USER $TARGET_USER WITH PASSWORD '$TARGET_PASS';"
              psql -d postgres -c "GRANT $TARGET_USER TO CURRENT_USER;"
              psql -d postgres -tc "SELECT 1 FROM pg_database WHERE datname='$TARGET_DB'" | grep -q 1 || \
                psql -d postgres -c "CREATE DATABASE $TARGET_DB OWNER $TARGET_USER;"
              psql -d postgres -c "GRANT ALL PRIVILEGES ON DATABASE $TARGET_DB TO $TARGET_USER;"
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
  }
}
