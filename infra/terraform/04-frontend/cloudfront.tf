# ══════════════════════════════════════════════════════════════════════
#  CloudFront Distribution — SPA com OAC para S3, sem domínio custom
#  • Usa *.cloudfront.net + cert default da AWS (grátis, sem ACM)
#  • SPA routing via custom_error_response 403/404 → /index.html (200)
#  • Security headers + CSP via Response Headers Policy
#  • HTTPS-only + TLS 1.2
# ══════════════════════════════════════════════════════════════════════

resource "aws_cloudfront_origin_access_control" "frontend" {
  name                              = "archlens-frontend-oac-${var.environment}"
  description                       = "OAC para bucket S3 do frontend ArchLens"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# ── Response Headers Policy: HSTS + CSP + security headers ───────────
resource "aws_cloudfront_response_headers_policy" "frontend" {
  name = "archlens-frontend-security-${var.environment}"

  security_headers_config {
    content_type_options { override = true }
    frame_options {
      frame_option = "DENY"
      override     = true
    }
    referrer_policy {
      referrer_policy = "strict-origin-when-cross-origin"
      override        = true
    }
    strict_transport_security {
      access_control_max_age_sec = 31536000
      include_subdomains         = true
      preload                    = true
      override                   = true
    }
    xss_protection {
      mode_block = true
      override   = true
      protection = true
    }
    content_security_policy {
      override = true
      content_security_policy = join("; ", [
        "default-src 'self'",
        "script-src 'self' 'unsafe-inline' https://*.clerk.accounts.dev https://clerk.accounts.dev https://*.clerk.com https://js.clerk.com https://challenges.cloudflare.com",
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
        "font-src 'self' https://fonts.gstatic.com data:",
        "img-src 'self' data: blob: https://img.clerk.com https://*.clerk.accounts.dev https://*.clerk.com",
        "connect-src 'self' ${local.api_gateway_url} https://*.clerk.accounts.dev https://clerk.accounts.dev https://*.clerk.com https://clerk-telemetry.com",
        "frame-src https://*.clerk.accounts.dev https://*.clerk.com https://challenges.cloudflare.com",
        "frame-ancestors 'none'",
        "worker-src 'self' blob:",
        "manifest-src 'self'",
        "media-src 'self' blob:",
        "object-src 'none'",
        "base-uri 'self'",
        "form-action 'self'",
        "upgrade-insecure-requests",
      ])
    }
  }
}

data "aws_cloudfront_cache_policy" "caching_optimized" {
  name = "Managed-CachingOptimized"
}

data "aws_cloudfront_cache_policy" "caching_disabled" {
  name = "Managed-CachingDisabled"
}

# ══════════════════════════════════════════════════════════════════════
#  Distribuição
# ══════════════════════════════════════════════════════════════════════
resource "aws_cloudfront_distribution" "frontend" {
  enabled             = true
  is_ipv6_enabled     = true
  http_version        = "http2and3"
  price_class         = var.price_class
  default_root_object = "index.html"
  comment             = "ArchLens frontend (${var.environment})"
  web_acl_id          = var.waf_web_acl_arn

  # Sem aliases — acesso somente via d<id>.cloudfront.net

  origin {
    origin_id                = "s3-frontend"
    domain_name              = aws_s3_bucket.frontend.bucket_regional_domain_name
    origin_access_control_id = aws_cloudfront_origin_access_control.frontend.id

    dynamic "origin_shield" {
      for_each = var.enable_origin_shield ? [1] : []
      content {
        enabled              = true
        origin_shield_region = var.origin_shield_region
      }
    }
  }

  # Logging via CloudFront Standard Logging v2 — definido em logs.tf
  # (aws_cloudwatch_log_delivery_*). O bloco logging_config legado foi
  # removido porque dependia de ACL log-delivery-write, incompatível
  # com bucket BucketOwnerEnforced.

  default_cache_behavior {
    target_origin_id       = "s3-frontend"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    compress               = true

    cache_policy_id            = data.aws_cloudfront_cache_policy.caching_optimized.id
    response_headers_policy_id = aws_cloudfront_response_headers_policy.frontend.id
  }

  ordered_cache_behavior {
    path_pattern           = "/index.html"
    target_origin_id       = "s3-frontend"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    compress               = true

    cache_policy_id            = data.aws_cloudfront_cache_policy.caching_disabled.id
    response_headers_policy_id = aws_cloudfront_response_headers_policy.frontend.id
  }

  custom_error_response {
    error_code            = 403
    response_code         = 200
    response_page_path    = "/index.html"
    error_caching_min_ttl = 10
  }

  custom_error_response {
    error_code            = 404
    response_code         = 200
    response_page_path    = "/index.html"
    error_caching_min_ttl = 10
  }

  # ── Certificado default *.cloudfront.net gerenciado pela AWS ────────
  # Quando cloudfront_default_certificate=true a TLS mínima é forçada em
  # TLSv1 pela própria AWS — não é possível sobrescrever.
  viewer_certificate {
    cloudfront_default_certificate = true
  }

  restrictions {
    geo_restriction { restriction_type = "none" }
  }

  tags = local.common_tags
}

# ── Métricas adicionais (cache-hit rate, 4xx/5xx por path, origin latency) ─
# Custo: ~$0.10 por métrica/distribuição/mês (ver pricing CloudFront).
# Consumíveis via CloudWatch e New Relic AWS API polling.
resource "aws_cloudfront_monitoring_subscription" "frontend" {
  distribution_id = aws_cloudfront_distribution.frontend.id
  monitoring_subscription {
    realtime_metrics_subscription_config {
      realtime_metrics_subscription_status = "Enabled"
    }
  }
}
