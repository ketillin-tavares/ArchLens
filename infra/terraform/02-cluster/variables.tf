# ── General ────────────────────────────────────────────────────────────
variable "aws_region" {
  type        = string
  default     = "us-east-2"
  description = "Região AWS — deve ser a mesma do workspace 01-foundation"
}

variable "environment" {
  type        = string
  default     = "dev"
  description = "Nome do ambiente (dev, staging, prod) — usado em tags para cost tracking e auditoria"
}

# ── EKS ────────────────────────────────────────────────────────────────
variable "eks_cluster_name" {
  type        = string
  default     = "archlens-cluster"
  description = "Nome do cluster EKS"
}

variable "eks_cluster_version" {
  type        = string
  default     = "1.32"
  description = "Versão do Kubernetes no EKS"
}

# ── Node Group ─────────────────────────────────────────────────────────
variable "node_instance_types" {
  type        = list(string)
  default     = ["t3.medium"]
  description = "Tipos de instância EC2 para os worker nodes"
}

variable "node_capacity_type" {
  type        = string
  default     = "SPOT"
  description = "Tipo de capacidade dos nodes (SPOT ~60% mais barato ou ON_DEMAND)"
}

variable "node_min_size" {
  type        = number
  default     = 2
  description = "Número mínimo de nodes no node group"
}

variable "node_max_size" {
  type        = number
  default     = 4
  description = "Número máximo de nodes no node group"
}

variable "node_desired_size" {
  type        = number
  default     = 3
  description = "Número desejado de nodes no node group. 3 nodes t3.medium (~5400m allocatable) acomodam plataforma (~1900m) + sistema (~700m) + services em min (6 pods × ~175m = ~1050m) com margem para scale-up moderado do HPA (upload → 6, report → 4). Para picos alem disso, ativar Cluster Autoscaler no 02-cluster ou subir para 4."
}

# ── ALB Controller ─────────────────────────────────────────────────────
variable "alb_controller_chart_version" {
  type        = string
  default     = "1.7.1"
  description = "Versão do Helm chart do AWS Load Balancer Controller"
}

# ── Metrics Server ─────────────────────────────────────────────────────
variable "metrics_server_chart_version" {
  type        = string
  default     = "3.12.1"
  description = "Versão do Helm chart do Metrics Server — pré-requisito para HPA"
}
