# ── VPC ────────────────────────────────────────────────────────────────
output "vpc_id" {
  value       = module.vpc.vpc_id
  description = "ID da VPC criada para o projeto ArchLens"
}

output "private_subnets" {
  value       = module.vpc.private_subnets
  description = "IDs das subnets privadas (EKS nodes, RDS)"
}

output "public_subnets" {
  value       = module.vpc.public_subnets
  description = "IDs das subnets públicas (ALB, NAT Gateway)"
}

# ── RDS ────────────────────────────────────────────────────────────────
output "rds_endpoint" {
  value       = module.rds.db_instance_endpoint
  sensitive   = true
  description = "Endpoint de conexão do RDS PostgreSQL (host:port)"
}

output "rds_address" {
  value       = module.rds.db_instance_address
  sensitive   = true
  description = "Hostname do RDS PostgreSQL (sem porta)"
}

# ── S3 ─────────────────────────────────────────────────────────────────
output "s3_bucket" {
  value       = aws_s3_bucket.diagramas.id
  description = "Nome do bucket S3 para upload de diagramas"
}

output "s3_bucket_arn" {
  value       = aws_s3_bucket.diagramas.arn
  description = "ARN do bucket S3 de diagramas — usado nas IAM policies dos serviços"
}

# ── ECR ────────────────────────────────────────────────────────────────
output "ecr_urls" {
  value       = { for k, v in aws_ecr_repository.services : k => v.repository_url }
  description = "URLs dos repositórios ECR por serviço (upload, processing, report)"
}

# ── IAM ────────────────────────────────────────────────────────────────
output "eks_cluster_role_arn" {
  value       = aws_iam_role.eks_cluster.arn
  description = "ARN do IAM role do EKS control plane — consumido pelo workspace 02-cluster"
}

output "eks_nodes_role_arn" {
  value       = aws_iam_role.eks_nodes.arn
  description = "ARN do IAM role dos EKS worker nodes — consumido pelo workspace 02-cluster"
}

output "upload_service_role_arn" {
  value       = aws_iam_role.upload_service_sa.arn
  description = "ARN do IRSA role do upload-service para acesso S3 (read/write)"
}

output "processing_service_role_arn" {
  value       = aws_iam_role.processing_service_sa.arn
  description = "ARN do IRSA role do processing-service para acesso S3 (read-only)"
}

output "alb_controller_role_arn" {
  value       = aws_iam_role.alb_controller.arn
  description = "ARN do IRSA role do AWS Load Balancer Controller"
}

output "ebs_csi_driver_role_arn" {
  value       = aws_iam_role.ebs_csi_driver.arn
  description = "ARN do IRSA role do EBS CSI Driver — consumido pelo addon no workspace 02-cluster"
}

# ── Security Groups ───────────────────────────────────────────────────
output "eks_nodes_sg_id" {
  value       = aws_security_group.eks_nodes.id
  description = "ID do Security Group dos EKS nodes — consumido pelo workspace 02-cluster"
}

# ── New Relic ──────────────────────────────────────────────────────────
output "newrelic_integration_role_arn" {
  value       = aws_iam_role.newrelic_integration.arn
  description = "ARN do IAM role para AWS API polling do New Relic — configurar no NR UI em Infrastructure > AWS"
}
