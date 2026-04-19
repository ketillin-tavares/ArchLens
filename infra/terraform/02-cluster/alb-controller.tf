# ── AWS Load Balancer Controller ──────────────────────────────────────
# Necessário para que Ingress resources criem ALBs reais na AWS.
# O role IAM (IRSA) foi criado no workspace 01-foundation.

resource "kubernetes_service_account" "alb_controller" {
  metadata {
    name      = "aws-load-balancer-controller"
    namespace = "kube-system"

    annotations = {
      "eks.amazonaws.com/role-arn" = local.alb_role_arn
    }

    labels = {
      "app.kubernetes.io/component" = "controller"
      "app.kubernetes.io/name"      = "aws-load-balancer-controller"
    }
  }
}

resource "helm_release" "alb_controller" {
  name       = "aws-load-balancer-controller"
  repository = "https://aws.github.io/eks-charts"
  chart      = "aws-load-balancer-controller"
  namespace  = "kube-system"
  version    = var.alb_controller_chart_version

  set = [
    {
      name  = "clusterName"
      value = module.eks.cluster_name
    },
    {
      name  = "serviceAccount.create"
      value = "false"
    },
    {
      name  = "serviceAccount.name"
      value = kubernetes_service_account.alb_controller.metadata[0].name
    },
    {
      name  = "region"
      value = var.aws_region
    },
    {
      name  = "vpcId"
      value = local.vpc_id
    },
  ]

  depends_on = [
    module.eks,
    kubernetes_service_account.alb_controller,
    aws_iam_openid_connect_provider.eks
  ]
}
