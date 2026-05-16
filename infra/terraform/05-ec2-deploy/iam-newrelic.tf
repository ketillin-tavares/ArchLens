# IAM role para AWS API polling do New Relic.
# Permite que o NR colete metricas nativas dos servicos AWS gerenciados
# (RDS, S3, EC2, VPC) via cross-account assume-role.
# Configurar no NR UI em Infrastructure > AWS apos terraform apply.

resource "aws_iam_role" "newrelic_integration" {
  name = "NewRelicInfrastructure-Integrations-EC2"

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

resource "aws_iam_role_policy_attachment" "newrelic_readonly" {
  policy_arn = "arn:aws:iam::aws:policy/ReadOnlyAccess"
  role       = aws_iam_role.newrelic_integration.name
}

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
