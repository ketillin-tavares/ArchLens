terraform {
  required_version = ">= 1.5"

  cloud {
    organization = "archlens"
    workspaces { name = "archlens-foundation" }
  }
  required_providers {
    aws    = { source = "hashicorp/aws", version = "~> 5.0" }
    random = { source = "hashicorp/random", version = "~> 3.6" }
  }
}

provider "aws" { region = var.aws_region }


data "aws_caller_identity" "current" {}


locals {
  common_tags = {
    Project     = "archlens"
    ManagedBy   = "terraform"
    Environment = var.environment
  }

  # Será preenchido com o OIDC issuer do EKS após o cluster existir.
  # Como este workspace roda antes do EKS, o OIDC provider é criado
  # no workspace 02-cluster e os IRSA roles acima só são efetivos depois.
  # O oidc_provider aqui é um placeholder; substituir pelo issuer real
  # obtido via: aws eks describe-cluster --name archlens-cluster --query "cluster.identity.oidc.issuer"
  oidc_provider = "oidc.eks.us-east-2.amazonaws.com/id/8B31A297F73AC76837681A545C1B92A3"
}
