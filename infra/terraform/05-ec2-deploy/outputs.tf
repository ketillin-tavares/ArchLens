# ── EC2 ────────────────────────────────────────────────────────────────
output "ec2_public_dns" {
  value       = aws_eip.archlens.public_dns
  description = "DNS publico fixo da EC2 (Opcao 1: usar este URL para acessar o frontend)"
}

output "ec2_public_ip" {
  value       = aws_eip.archlens.public_ip
  description = "Elastic IP fixo da EC2"
}

output "ec2_instance_id" {
  value       = aws_instance.archlens.id
  description = "ID da EC2 (usar com SSM Session Manager: aws ssm start-session --target <id>)"
}

output "frontend_url" {
  value       = "http://${aws_eip.archlens.public_dns}"
  description = "URL completa do frontend (HTTP only — Clerk DEV mode)"
}

output "kong_api_url" {
  value       = "http://${aws_eip.archlens.public_dns}:8000"
  description = "URL do Kong API gateway"
}

# ── RDS ────────────────────────────────────────────────────────────────
output "rds_endpoint" {
  value       = module.rds.db_instance_endpoint
  sensitive   = true
  description = "Endpoint de conexao do RDS PostgreSQL"
}

output "rds_address" {
  value       = module.rds.db_instance_address
  sensitive   = true
  description = "Hostname do RDS PostgreSQL"
}

# ── S3 ─────────────────────────────────────────────────────────────────
output "s3_bucket" {
  value       = aws_s3_bucket.diagramas.id
  description = "Nome do bucket S3 de diagramas"
}

output "s3_bucket_arn" {
  value       = aws_s3_bucket.diagramas.arn
  description = "ARN do bucket S3 de diagramas"
}

# ── ECR ────────────────────────────────────────────────────────────────
output "ecr_urls" {
  value       = { for k, v in aws_ecr_repository.services : k => v.repository_url }
  description = "URLs dos repositorios ECR (consumido pelo GitHub Actions)"
}

output "ecr_registry" {
  value       = local.ecr_registry
  description = "Endpoint do registry ECR (usado em docker login)"
}

# ── Secrets Manager ────────────────────────────────────────────────────
output "secret_arns" {
  value       = { for k, v in aws_secretsmanager_secret.archlens : k => v.arn }
  description = "ARNs dos secrets criados (preencher valores via console ou CLI)"
}

# ── IAM ────────────────────────────────────────────────────────────────
output "ec2_iam_role_arn" {
  value       = aws_iam_role.ec2.arn
  description = "ARN do IAM role da EC2"
}

output "newrelic_integration_role_arn" {
  value       = aws_iam_role.newrelic_integration.arn
  description = "ARN do IAM role para AWS API polling do New Relic"
}

# ── VPC ────────────────────────────────────────────────────────────────
output "vpc_id" {
  value       = module.vpc.vpc_id
  description = "ID da VPC criada para o stack EC2"
}
