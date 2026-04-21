output "s3_bucket_name" {
  value       = aws_s3_bucket.frontend.bucket
  description = "Bucket S3 destino do deploy (aws s3 sync dist/)"
}

output "cloudfront_distribution_id" {
  value       = aws_cloudfront_distribution.frontend.id
  description = "ID da distribuição CloudFront — usado em `aws cloudfront create-invalidation`"
}

output "cloudfront_domain_name" {
  value       = aws_cloudfront_distribution.frontend.domain_name
  description = "Domínio *.cloudfront.net da distribuição (URL pública do frontend)"
}

output "frontend_url" {
  value       = "https://${aws_cloudfront_distribution.frontend.domain_name}"
  description = "URL final do frontend — use esse valor no CORS do Kong (origins) em prod"
}

output "ssm_parameter_prefix" {
  value       = local.ssm_prefix
  description = "Prefixo SSM onde estão as chaves de build — usado pelo workflow frontend-deploy"
}

output "cloudfront_logs_bucket" {
  value       = var.enable_access_logs ? aws_s3_bucket.logs[0].bucket : null
  description = "Bucket S3 onde a CloudFront escreve access logs (null se logs desabilitados)"
}
