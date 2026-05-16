terraform {
  required_version = ">= 1.5"

  cloud {
    organization = "archlens"
    workspaces { name = "archlens-ec2-deploy" }
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
    Stack       = "ec2-deploy"
  }
}

resource "random_id" "suffix" { byte_length = 4 }
