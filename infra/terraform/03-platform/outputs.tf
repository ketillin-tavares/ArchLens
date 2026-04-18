# ── Vault ──────────────────────────────────────────────────────────────
output "vault_url" {
  value       = var.vault_service_type == "LoadBalancer" ? "http://${data.kubernetes_service.vault.status[0].load_balancer[0].ingress[0].hostname}:8200" : "http://vault.archlens.svc.cluster.local:8200"
  description = "URL do Vault — LoadBalancer para bootstrap ou DNS interno após restringir para ClusterIP"
}

# ── RabbitMQ ───────────────────────────────────────────────────────────
output "rabbitmq_connection_url" {
  value       = "amqp://archlens:<PASSWORD>@rabbitmq.archlens.svc.cluster.local:5672/"
  description = "Connection string do RabbitMQ (substituir <PASSWORD> pelo valor do output rabbitmq_password)"
}

output "rabbitmq_password" {
  value       = var.rabbitmq_password
  sensitive   = true
  description = "Senha do usuario archlens no RabbitMQ — recuperar via: terraform output -raw rabbitmq_password"
}

# ── Kong ───────────────────────────────────────────────────────────────
output "kong_url" {
  value       = "http://${data.kubernetes_service.kong.status[0].load_balancer[0].ingress[0].hostname}"
  description = "URL pública do Kong — endpoint da API para clientes externos"
}

# ── LiteLLM ────────────────────────────────────────────────────────────
output "litellm_internal_url" {
  value       = "http://litellm-proxy.archlens.svc.cluster.local:4000"
  description = "URL interna do LiteLLM Proxy — usada pelo processing-service via DNS K8s"
}
