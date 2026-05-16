# VPC minima para o stack EC2.
# Diferente do foundation: SEM NAT Gateway (economia ~$32/mes), sem tags
# de auto-discovery EKS, e apenas 1 subnet publica (a EC2 vive nela).
# RDS exige 2 subnets em AZs diferentes — por isso ha 2 privadas mesmo
# nao havendo necessidade de saida pra internet de la.

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.5.1"

  name = "archlens-ec2-vpc"
  cidr = var.vpc_cidr

  azs             = ["${var.aws_region}a", "${var.aws_region}b"]
  public_subnets  = [var.public_subnet_cidr, cidrsubnet(var.vpc_cidr, 8, 2)]
  private_subnets = var.private_subnet_cidrs

  # SEM NAT Gateway — RDS nao precisa de egress, EC2 fica em publica
  enable_nat_gateway   = false
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = local.common_tags
}
