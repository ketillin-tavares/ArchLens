module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "20.8.4"

  cluster_name    = var.eks_cluster_name
  cluster_version = var.eks_cluster_version

  vpc_id     = local.vpc_id
  subnet_ids = local.private_subnets

  cluster_endpoint_public_access  = true
  cluster_endpoint_private_access = true

  # Concede admin access (via EKS Access Entries) ao IAM identity que cria o cluster.
  # Sem isso, o terraform runner não consegue criar recursos kubernetes_* (Unauthorized).
  enable_cluster_creator_admin_permissions = true

  # Usar role IAM criado no workspace foundation
  iam_role_arn = local.cluster_role

  # Add-ons gerenciados pela AWS (atualizados automaticamente)
  cluster_addons = {
    coredns    = { most_recent = true }
    kube-proxy = { most_recent = true }
    vpc-cni    = { most_recent = true }
    # EBS CSI driver — necessário para PVCs (Vault precisa de storage)
    aws-ebs-csi-driver = { most_recent = true }
  }

  eks_managed_node_groups = {
    default = {
      name           = "archlens-nodes"
      instance_types = var.node_instance_types
      capacity_type  = var.node_capacity_type

      min_size     = var.node_min_size
      max_size     = var.node_max_size
      desired_size = var.node_desired_size

      iam_role_arn    = local.nodes_role
      create_iam_role = false

      # Nodes nas subnets privadas (sem exposição à internet)
      subnet_ids = local.private_subnets

      vpc_security_group_ids = [local.nodes_sg_id]

      labels = {
        role    = "worker"
        project = "archlens"
      }

      tags = merge(local.common_tags, { NodeGroup = "default" })
    }
  }

  tags = local.common_tags
}
