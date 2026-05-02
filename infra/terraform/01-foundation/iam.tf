# ── IAM: EKS Cluster Role ─────────────────────────────────────────────
# Necessário para o plano de controle do EKS chamar serviços AWS
resource "aws_iam_role" "eks_cluster" {
  name = "archlens-eks-cluster-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "eks.amazonaws.com" }
    }]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "eks_cluster_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.eks_cluster.name
}

# ── IAM: EKS Node Group Role ──────────────────────────────────────────
# EC2 nodes precisam de 3 políticas obrigatórias para participar do cluster
resource "aws_iam_role" "eks_nodes" {
  name = "archlens-eks-nodes-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
    }]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "eks_worker_node_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
  role       = aws_iam_role.eks_nodes.name
}

resource "aws_iam_role_policy_attachment" "eks_cni_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
  role       = aws_iam_role.eks_nodes.name
}

resource "aws_iam_role_policy_attachment" "ecr_readonly" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
  role       = aws_iam_role.eks_nodes.name
}

# New Relic Infrastructure Agent nos nodes precisa de SSM (opcional, mas recomendado)
resource "aws_iam_role_policy_attachment" "ssm_managed" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
  role       = aws_iam_role.eks_nodes.name
}

# ── IAM: IRSA — upload-service (acesso S3) ────────────────────────────
# IRSA = IAM Roles for Service Accounts
# Permite que o pod do upload-service acesse o S3 sem chaves hardcoded
resource "aws_iam_role" "upload_service_sa" {
  name = "archlens-upload-service-sa-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = "sts:AssumeRoleWithWebIdentity"
      Principal = {
        Federated = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:oidc-provider/${local.oidc_provider}"
      }
      Condition = {
        StringEquals = {
          "${local.oidc_provider}:sub" = "system:serviceaccount:archlens:upload-service-sa"
          "${local.oidc_provider}:aud" = "sts.amazonaws.com"
        }
      }
    }]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy" "upload_service_s3" {
  name = "archlens-upload-service-s3-policy"
  role = aws_iam_role.upload_service_sa.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.diagramas.arn,
          "${aws_s3_bucket.diagramas.arn}/*"
        ]
      }
    ]
  })
}

# ── IAM: IRSA — processing-service (acesso S3 leitura) ───────────────
resource "aws_iam_role" "processing_service_sa" {
  name = "archlens-processing-service-sa-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = "sts:AssumeRoleWithWebIdentity"
      Principal = {
        Federated = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:oidc-provider/${local.oidc_provider}"
      }
      Condition = {
        StringEquals = {
          "${local.oidc_provider}:sub" = "system:serviceaccount:archlens:processing-service-sa"
          "${local.oidc_provider}:aud" = "sts.amazonaws.com"
        }
      }
    }]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy" "processing_service_s3" {
  name = "archlens-processing-service-s3-policy"
  role = aws_iam_role.processing_service_sa.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = ["s3:GetObject", "s3:ListBucket"]
        Resource = [
          aws_s3_bucket.diagramas.arn,
          "${aws_s3_bucket.diagramas.arn}/*"
        ]
      }
    ]
  })
}

# ── IAM: AWS Load Balancer Controller ─────────────────────────────────
# O ALB Ingress Controller precisa criar/gerenciar ALBs e Target Groups
resource "aws_iam_role" "alb_controller" {
  name = "archlens-alb-controller-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = "sts:AssumeRoleWithWebIdentity"
      Principal = {
        Federated = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:oidc-provider/${local.oidc_provider}"
      }
      Condition = {
        StringEquals = {
          "${local.oidc_provider}:sub" = "system:serviceaccount:kube-system:aws-load-balancer-controller"
          "${local.oidc_provider}:aud" = "sts.amazonaws.com"
        }
      }
    }]
  })

  tags = local.common_tags
}

# Política oficial da AWS para o ALB Controller
resource "aws_iam_policy" "alb_controller" {
  name   = "archlens-alb-controller-policy"
  policy = file("${path.module}/alb-controller-policy.json")
}

resource "aws_iam_role_policy_attachment" "alb_controller" {
  policy_arn = aws_iam_policy.alb_controller.arn
  role       = aws_iam_role.alb_controller.name
}

# ── IAM: EBS CSI Driver (IRSA) ────────────────────────────────────────
# O EBS CSI Driver controller precisa de permissão para criar/anexar volumes EBS
# para PersistentVolumes. Sem este IRSA o addon entra em CrashLoopBackOff.
resource "aws_iam_role" "ebs_csi_driver" {
  name = "archlens-ebs-csi-driver-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = "sts:AssumeRoleWithWebIdentity"
      Principal = {
        Federated = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:oidc-provider/${local.oidc_provider}"
      }
      Condition = {
        StringEquals = {
          "${local.oidc_provider}:sub" = "system:serviceaccount:kube-system:ebs-csi-controller-sa"
          "${local.oidc_provider}:aud" = "sts.amazonaws.com"
        }
      }
    }]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "ebs_csi_driver" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy"
  role       = aws_iam_role.ebs_csi_driver.name
}

# ── IAM: New Relic AWS API Polling ────────────────────────────────────
# Permite que o New Relic colete métricas nativas dos serviços gerenciados
# (RDS, S3, ALB, NAT Gateway, VPC) via AWS API polling.
# Docs: https://docs.newrelic.com/docs/infrastructure/amazon-integrations/connect/set-up-aws-api-polling/
resource "aws_iam_role" "newrelic_integration" {
  name = "NewRelicInfrastructure-Integrations"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = "sts:AssumeRole"
      Principal = {
        AWS = "arn:aws:iam::754728514883:root"
      }
      Condition = {
        StringEquals = {
          "sts:ExternalId" = var.newrelic_account_id
        }
      }
    }]
  })

  tags = local.common_tags
}

# ReadOnlyAccess — permite que o New Relic leia métricas de todos os serviços AWS
resource "aws_iam_role_policy_attachment" "newrelic_readonly" {
  policy_arn = "arn:aws:iam::aws:policy/ReadOnlyAccess"
  role       = aws_iam_role.newrelic_integration.name
}

# Budgets — permite visualizar custos (opcional mas recomendado)
resource "aws_iam_role_policy" "newrelic_budgets" {
  name = "archlens-newrelic-budgets-policy"
  role = aws_iam_role.newrelic_integration.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["budgets:ViewBudget"]
      Resource = "*"
    }]
  })
}
