terraform {
  required_version = ">= 1.5"

  cloud {
    organization = "archlens"
    workspaces { name = "archlens-platform" }
  }
  required_providers {
    aws        = { source = "hashicorp/aws", version = "~> 5.0" }
    helm       = { source = "hashicorp/helm", version = "~> 2.12" }
    kubernetes = { source = "hashicorp/kubernetes", version = "~> 2.27" }
  }
}

provider "aws" { region = var.aws_region }

# ── Leitura dos workspaces anteriores ────────────────────────────────
data "terraform_remote_state" "foundation" {
  backend = "remote"
  config = {
    organization = "archlens"
    workspaces   = { name = "archlens-foundation" }
  }
}

data "terraform_remote_state" "cluster" {
  backend = "remote"
  config = {
    organization = "archlens"
    workspaces   = { name = "archlens-cluster" }
  }
}

# ── Autenticação Kubernetes/Helm via EKS ─────────────────────────────
data "aws_eks_cluster_auth" "cluster" {
  name = local.cluster_name
}

provider "kubernetes" {
  host                   = local.cluster_endpoint
  cluster_ca_certificate = base64decode(local.cluster_ca)
  token                  = data.aws_eks_cluster_auth.cluster.token
}

provider "helm" {
  kubernetes {
    host                   = local.cluster_endpoint
    cluster_ca_certificate = base64decode(local.cluster_ca)
    token                  = data.aws_eks_cluster_auth.cluster.token
  }
}

# ── Locals ────────────────────────────────────────────────────────────
locals {
  # Outputs do workspace 01-foundation
  s3_bucket   = data.terraform_remote_state.foundation.outputs.s3_bucket
  rds_address = data.terraform_remote_state.foundation.outputs.rds_address

  # Outputs do workspace 02-cluster
  cluster_name     = data.terraform_remote_state.cluster.outputs.cluster_name
  cluster_endpoint = data.terraform_remote_state.cluster.outputs.cluster_endpoint
  cluster_ca       = data.terraform_remote_state.cluster.outputs.cluster_ca

  common_tags = {
    Project     = "archlens"
    ManagedBy   = "terraform"
    Environment = var.environment
  }
}

# ── Namespace archlens ───────────────────────────────────────────────
# Referência ao namespace criado no 02-cluster.
# Usado como dependência pelos Helm releases deste workspace.
data "kubernetes_namespace" "archlens" {
  metadata {
    name = "archlens"
  }
}
