terraform {
  required_version = ">= 1.5"

  cloud {
    organization = "archlens"
    workspaces { name = "archlens-cluster" }
  }
  required_providers {
    aws        = { source = "hashicorp/aws", version = "~> 5.0" }
    helm       = { source = "hashicorp/helm", version = "~> 3.0" }
    kubernetes = { source = "hashicorp/kubernetes", version = "~> 2.27" }
    tls        = { source = "hashicorp/tls", version = "~> 4.0" }
  }
}

provider "aws" { region = var.aws_region }

data "terraform_remote_state" "foundation" {
  backend = "remote"
  config = {
    organization = "archlens"
    workspaces   = { name = "archlens-foundation" }
  }
}

data "aws_eks_cluster_auth" "cluster" {
  name = module.eks.cluster_name
}

provider "kubernetes" {
  host                   = module.eks.cluster_endpoint
  cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)
  token                  = data.aws_eks_cluster_auth.cluster.token
}

provider "helm" {
  kubernetes = {
    host                   = module.eks.cluster_endpoint
    cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)
    token                  = data.aws_eks_cluster_auth.cluster.token
  }
}

# ── Locals ────────────────────────────────────────────────────────────
locals {
  # Outputs do workspace 01-foundation
  vpc_id           = data.terraform_remote_state.foundation.outputs.vpc_id
  private_subnets  = data.terraform_remote_state.foundation.outputs.private_subnets
  public_subnets   = data.terraform_remote_state.foundation.outputs.public_subnets
  cluster_role     = data.terraform_remote_state.foundation.outputs.eks_cluster_role_arn
  nodes_role       = data.terraform_remote_state.foundation.outputs.eks_nodes_role_arn
  alb_role_arn     = data.terraform_remote_state.foundation.outputs.alb_controller_role_arn
  ebs_csi_role_arn = data.terraform_remote_state.foundation.outputs.ebs_csi_driver_role_arn
  nodes_sg_id      = data.terraform_remote_state.foundation.outputs.eks_nodes_sg_id

  common_tags = {
    Project     = "archlens"
    ManagedBy   = "terraform"
    Environment = var.environment
  }
}
