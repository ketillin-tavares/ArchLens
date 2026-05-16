data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# user-data: roda apenas na primeira boot. Instala Docker, awscli, git,
# clona o repositorio e dispara o bootstrap inicial.
locals {
  ecr_registry = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.aws_region}.amazonaws.com"

  user_data = templatefile("${path.module}/user-data.sh.tftpl", {
    aws_region         = var.aws_region
    environment        = var.environment
    github_repo_url    = var.github_repo_url
    github_branch      = var.github_branch
    rds_address        = module.rds.db_instance_address
    db_master_password = var.db_master_password
    s3_bucket          = aws_s3_bucket.diagramas.id
    ecr_registry       = local.ecr_registry
  })
}

resource "aws_instance" "archlens" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.ec2_instance_type
  key_name               = var.ec2_key_name
  subnet_id              = module.vpc.public_subnets[0]
  vpc_security_group_ids = [aws_security_group.ec2.id]
  iam_instance_profile   = aws_iam_instance_profile.ec2.name

  associate_public_ip_address = true
  user_data                   = local.user_data
  user_data_replace_on_change = false

  # Spot Instance — persistent + stop preserva o EBS root e reinicia
  # automaticamente quando capacidade volta. Containers retomam via
  # restart: unless-stopped do compose. Elastic IP mantem o DNS.
  dynamic "instance_market_options" {
    for_each = var.ec2_use_spot ? [1] : []
    content {
      market_type = "spot"
      spot_options {
        spot_instance_type             = "persistent"
        instance_interruption_behavior = "stop"
        max_price                      = var.ec2_spot_max_price != "" ? var.ec2_spot_max_price : null
      }
    }
  }

  root_block_device {
    volume_type = "gp3"
    volume_size = var.ec2_root_volume_size
    encrypted   = true
  }

  metadata_options {
    http_tokens   = "required"
    http_endpoint = "enabled"
  }

  tags = merge(local.common_tags, { Name = "archlens-ec2" })

  lifecycle {
    # user-data e mudancas em locals nao recriam a instancia. Updates de
    # servico sao feitos via SSH + docker compose, nao via terraform.
    ignore_changes = [user_data, ami]
  }

  depends_on = [
    module.rds,
    aws_secretsmanager_secret_version.archlens,
  ]
}

resource "aws_eip" "archlens" {
  domain   = "vpc"
  instance = aws_instance.archlens.id

  tags = merge(local.common_tags, { Name = "archlens-ec2-eip" })
}
