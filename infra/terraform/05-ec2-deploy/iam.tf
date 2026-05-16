# IAM role + instance profile da EC2.
# Permissoes:
#   - Ler secrets em archlens/<env>/*
#   - Atualizar (PutSecretValue) os secrets processing e report,
#     usados pelo bootstrap-litellm-vk.sh
#   - R/W no bucket S3 de diagramas
#   - Pull de imagens do ECR
#   - SSM Session Manager (acesso shell sem SSH)

resource "aws_iam_role" "ec2" {
  name = "archlens-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy" "secrets_read" {
  name = "secrets-read"
  role = aws_iam_role.ec2.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret",
      ]
      Resource = [
        for s in aws_secretsmanager_secret.archlens : s.arn
      ]
    }]
  })
}

resource "aws_iam_role_policy" "secrets_write_vk" {
  name = "secrets-write-vk"
  role = aws_iam_role.ec2.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "secretsmanager:PutSecretValue",
        "secretsmanager:UpdateSecret",
      ]
      Resource = [
        aws_secretsmanager_secret.archlens["processing"].arn,
        aws_secretsmanager_secret.archlens["report"].arn,
      ]
    }]
  })
}

resource "aws_iam_role_policy" "s3_rw" {
  name = "s3-diagramas-rw"
  role = aws_iam_role.ec2.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
        ]
        Resource = "${aws_s3_bucket.diagramas.arn}/*"
      },
      {
        Effect   = "Allow"
        Action   = ["s3:ListBucket", "s3:GetBucketLocation"]
        Resource = aws_s3_bucket.diagramas.arn
      },
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecr_readonly" {
  role       = aws_iam_role.ec2.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

resource "aws_iam_role_policy_attachment" "ssm" {
  role       = aws_iam_role.ec2.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "ec2" {
  name = "archlens-ec2-profile"
  role = aws_iam_role.ec2.name

  tags = local.common_tags
}
