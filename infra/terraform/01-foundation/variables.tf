# ── General ────────────────────────────────────────────────────────────
variable "aws_region" {
  type        = string
  default     = "us-east-2"
  description = "Região AWS onde os recursos serão provisionados"
}

variable "environment" {
  type        = string
  default     = "dev"
  description = "Nome do ambiente (dev, staging, prod) — usado em tags para cost tracking e auditoria"
}

# ── VPC ────────────────────────────────────────────────────────────────
variable "vpc_cidr" {
  type        = string
  default     = "10.0.0.0/16"
  description = "CIDR block principal da VPC"
}

variable "private_subnet_cidrs" {
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
  description = "CIDRs das subnets privadas (uma por AZ)"
}

variable "public_subnet_cidrs" {
  type        = list(string)
  default     = ["10.0.101.0/24", "10.0.102.0/24"]
  description = "CIDRs das subnets públicas (uma por AZ)"
}

variable "eks_cluster_name" {
  type        = string
  default     = "archlens-cluster"
  description = "Nome do cluster EKS — usado nas tags de auto-discovery das subnets"
}

# ── RDS ────────────────────────────────────────────────────────────────
variable "db_password" {
  type        = string
  sensitive   = true
  description = "Senha do PostgreSQL — configurar como variável sensível no Terraform Cloud workspace"
}

variable "rds_engine_version" {
  type        = string
  default     = "16.2"
  description = "Versão do PostgreSQL para a instância RDS"
}

variable "rds_instance_class" {
  type        = string
  default     = "db.t3.micro"
  description = "Classe da instância RDS (db.t3.micro para free tier / dev)"
}

variable "rds_allocated_storage" {
  type        = number
  default     = 20
  description = "Armazenamento alocado em GB para a instância RDS"
}

# ── S3 ─────────────────────────────────────────────────────────────────
variable "s3_expiration_days" {
  type        = number
  default     = 30
  description = "Dias para expiração automática dos diagramas no S3"
}

# ── New Relic ──────────────────────────────────────────────────────────
variable "newrelic_account_id" {
  type        = string
  sensitive   = true
  description = "New Relic Account ID — usado como External ID na trust policy do IAM role de AWS API polling"
}
