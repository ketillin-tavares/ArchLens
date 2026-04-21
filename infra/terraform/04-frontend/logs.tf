# ══════════════════════════════════════════════════════════════════════
#  CloudFront Access Logs — bucket dedicado + lifecycle
#  • CloudFront Standard Logging v2 (via CloudWatch Logs delivery)
#  • Ownership = BucketOwnerEnforced (ACLs desabilitadas — prática atual
#    recomendada pela AWS; o padrão log-delivery-write via ACL está
#    deprecated e quebra em contas novas com ACLs off por default).
#  • Entrega autorizada por bucket policy para o principal do serviço
#    `delivery.logs.amazonaws.com`.
#  • Lifecycle: transição IA-30d, expiração configurável (default 90d).
#  • Bloqueio de acesso público total.
# ══════════════════════════════════════════════════════════════════════

resource "aws_s3_bucket" "logs" {
  count  = var.enable_access_logs ? 1 : 0
  bucket = "${local.bucket_name}-logs"
  # Mesma lógica do bucket principal: em dev/staging permite teardown
  # automático; em prod exige limpeza explícita de logs antes de destruir.
  force_destroy = var.environment != "prod"

  tags = local.common_tags
}

resource "aws_s3_bucket_ownership_controls" "logs" {
  count  = var.enable_access_logs ? 1 : 0
  bucket = aws_s3_bucket.logs[0].id
  rule { object_ownership = "BucketOwnerEnforced" }
}

resource "aws_s3_bucket_public_access_block" "logs" {
  count  = var.enable_access_logs ? 1 : 0
  bucket = aws_s3_bucket.logs[0].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "logs" {
  count  = var.enable_access_logs ? 1 : 0
  bucket = aws_s3_bucket.logs[0].id
  rule {
    apply_server_side_encryption_by_default { sse_algorithm = "AES256" }
  }
}

# ── Bucket policy para AWS Log Delivery Service ───────────────────────
# Substitui a ACL log-delivery-write. O serviço de entrega precisa de
# s3:GetBucketAcl (check de permissão) + s3:PutObject (gravação dos logs).
data "aws_iam_policy_document" "logs" {
  count = var.enable_access_logs ? 1 : 0

  statement {
    sid    = "AWSLogDeliveryAclCheck"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["delivery.logs.amazonaws.com"]
    }

    actions   = ["s3:GetBucketAcl"]
    resources = [aws_s3_bucket.logs[0].arn]
  }

  statement {
    sid    = "AWSLogDeliveryWrite"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["delivery.logs.amazonaws.com"]
    }

    actions   = ["s3:PutObject"]
    resources = ["${aws_s3_bucket.logs[0].arn}/*"]

    condition {
      test     = "StringEquals"
      variable = "s3:x-amz-acl"
      values   = ["bucket-owner-full-control"]
    }
  }
}

resource "aws_s3_bucket_policy" "logs" {
  count  = var.enable_access_logs ? 1 : 0
  bucket = aws_s3_bucket.logs[0].id
  policy = data.aws_iam_policy_document.logs[0].json
}

resource "aws_s3_bucket_lifecycle_configuration" "logs" {
  count  = var.enable_access_logs ? 1 : 0
  bucket = aws_s3_bucket.logs[0].id

  rule {
    id     = "expire-old-logs"
    status = "Enabled"
    filter {}

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    expiration {
      days = var.log_retention_days
    }
  }
}

# ══════════════════════════════════════════════════════════════════════
#  CloudFront Standard Logging v2 — via CloudWatch Logs delivery chain
#  Fonte → Destino → Delivery. A distribuição expõe ACCESS_LOGS e o
#  destino S3 é autorizado via bucket policy acima.
# ══════════════════════════════════════════════════════════════════════
resource "aws_cloudwatch_log_delivery_source" "frontend" {
  count        = var.enable_access_logs ? 1 : 0
  name         = "archlens-frontend-${var.environment}-cf-source"
  resource_arn = aws_cloudfront_distribution.frontend.arn
  log_type     = "ACCESS_LOGS"
}

resource "aws_cloudwatch_log_delivery_destination" "frontend" {
  count         = var.enable_access_logs ? 1 : 0
  name          = "archlens-frontend-${var.environment}-cf-dest"
  output_format = "plain"

  delivery_destination_configuration {
    destination_resource_arn = aws_s3_bucket.logs[0].arn
  }
}

resource "aws_cloudwatch_log_delivery" "frontend" {
  count                    = var.enable_access_logs ? 1 : 0
  delivery_source_name     = aws_cloudwatch_log_delivery_source.frontend[0].name
  delivery_destination_arn = aws_cloudwatch_log_delivery_destination.frontend[0].arn

  s3_delivery_configuration {
    suffix_path = "cloudfront/"
  }

  depends_on = [aws_s3_bucket_policy.logs]
}
