# ── General ────────────────────────────────────────────────────────────
variable "aws_region" {
  type        = string
  default     = "us-east-2"
  description = "Regiao AWS onde os recursos serao provisionados"
}

variable "environment" {
  type        = string
  default     = "dev"
  description = "Nome do ambiente (dev, staging, prod) — usado em tags e nome dos secrets"
}

# ── VPC ────────────────────────────────────────────────────────────────
variable "vpc_cidr" {
  type        = string
  default     = "10.10.0.0/16"
  description = "CIDR da VPC do stack EC2 (diferente do foundation 10.0.0.0/16 para evitar colisao)"
}

variable "public_subnet_cidr" {
  type        = string
  default     = "10.10.1.0/24"
  description = "CIDR da subnet publica onde a EC2 sera lancada"
}

variable "private_subnet_cidrs" {
  type        = list(string)
  default     = ["10.10.11.0/24", "10.10.12.0/24"]
  description = "CIDRs das subnets privadas (2 AZs — exigencia do RDS subnet group)"
}

# ── EC2 ────────────────────────────────────────────────────────────────
variable "ec2_instance_type" {
  type        = string
  default     = "t3.large"
  description = "Tipo da instancia EC2 (t3.large recomendado para 10+ containers)"
}

variable "ec2_root_volume_size" {
  type        = number
  default     = 50
  description = "Tamanho do volume root EBS em GB (imagens Docker + logs)"
}

variable "ec2_use_spot" {
  type        = bool
  default     = true
  description = "Usa Spot Instance (persistent + stop) para economizar ~70%. Em interrupcao a instancia e parada (nao terminada), EBS preservado e ela reinicia quando capacidade voltar."
}

variable "ec2_spot_max_price" {
  type        = string
  default     = ""
  description = "Preco maximo do spot por hora (USD). Vazio = preco on-demand como teto, evitando que o lance falhe."
}

variable "ec2_key_name" {
  type        = string
  description = "Nome da key pair AWS para acesso SSH (criar previamente no console EC2)"
}

variable "allowed_ssh_cidr" {
  type        = string
  description = "CIDR autorizado a acessar SSH (porta 22). Use seu IP publico /32"
}

# ── RDS ────────────────────────────────────────────────────────────────
variable "rds_engine_version" {
  type        = string
  default     = "18.3"
  description = "Versao do PostgreSQL para a instancia RDS"
}

variable "rds_instance_class" {
  type        = string
  default     = "db.t4g.micro"
  description = "Classe da instancia RDS"
}

variable "rds_allocated_storage" {
  type        = number
  default     = 20
  description = "Armazenamento alocado em GB para a instancia RDS"
}

variable "db_master_password" {
  type        = string
  sensitive   = true
  description = "Senha do master user 'archlens' do RDS — configurar no Terraform Cloud workspace"
}

# ── S3 ─────────────────────────────────────────────────────────────────
variable "s3_expiration_days" {
  type        = number
  default     = 30
  description = "Dias para expiracao automatica dos diagramas no S3"
}

# ── Repo ───────────────────────────────────────────────────────────────
variable "github_repo_url" {
  type        = string
  default     = "https://github.com/ketillin-tavares/ArchLens.git"
  description = "URL do repositorio Git para clonar na EC2"
}

variable "github_branch" {
  type        = string
  default     = "main"
  description = "Branch a ser usada no clone inicial"
}

# ── New Relic ──────────────────────────────────────────────────────────
variable "newrelic_account_id" {
  type        = string
  sensitive   = true
  description = "New Relic Account ID — usado como External ID na trust policy do IAM role de polling"
}
