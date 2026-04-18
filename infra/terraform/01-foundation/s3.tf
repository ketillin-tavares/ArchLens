resource "random_id" "suffix" { byte_length = 4 }

resource "aws_s3_bucket" "diagramas" {
  bucket = "archlens-diagramas-${random_id.suffix.hex}"
  tags   = local.common_tags
}

resource "aws_s3_bucket_lifecycle_configuration" "diagramas" {
  bucket = aws_s3_bucket.diagramas.id

  rule {
    id     = "expire-old-diagramas"
    status = "Enabled"

    expiration { days = var.s3_expiration_days }

    filter { prefix = "" }
  }
}

resource "aws_s3_bucket_public_access_block" "diagramas" {
  bucket                  = aws_s3_bucket.diagramas.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
