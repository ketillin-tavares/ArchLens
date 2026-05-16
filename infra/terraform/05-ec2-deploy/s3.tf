resource "aws_s3_bucket" "diagramas" {
  bucket = "archlens-ec2-diagramas-${random_id.suffix.hex}"
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

# CloudWatch Request Metrics — habilita as metricas /minuto que o NR
# consome (AllRequests, 4xxErrors, 5xxErrors, BytesUploaded/Downloaded,
# FirstByteLatency, TotalRequestLatency). Sem esse bloco S3 so emite
# Storage Metrics (BucketSizeBytes, NumberOfObjects) com cadencia diaria.
# Custo: ~$0.30 por milhao de requests (S3 Request Metrics tier).
resource "aws_s3_bucket_metric" "diagramas_requests" {
  bucket = aws_s3_bucket.diagramas.id
  name   = "EntireBucket"
}

# CORS para permitir que a SPA (servida em http://<ec2_dns>) consuma
# arquivos via presigned URL diretamente do S3. Sem isso, o browser
# bloqueia o fetch da origin do frontend.
resource "aws_s3_bucket_cors_configuration" "diagramas" {
  bucket = aws_s3_bucket.diagramas.id

  cors_rule {
    allowed_methods = ["GET", "HEAD"]
    allowed_origins = ["*"]
    allowed_headers = ["*"]
    expose_headers  = ["ETag", "Content-Length", "Content-Type"]
    max_age_seconds = 3000
  }
}
