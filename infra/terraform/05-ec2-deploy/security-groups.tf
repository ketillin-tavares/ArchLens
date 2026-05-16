# SG da EC2 — abre HTTP/HTTPS e Kong para o mundo, SSH so do CIDR autorizado.
# Portas internas dos containers (Postgres, RabbitMQ, admin do Kong, LiteLLM)
# NAO sao expostas publicamente.
resource "aws_security_group" "ec2" {
  name        = "archlens-ec2-sg"
  description = "Allow HTTP/HTTPS public, SSH restricted, all containers internal"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Frontend (nginx)"
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Frontend HTTPS (reservado para upgrade futuro)"
  }

  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Kong API gateway"
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.allowed_ssh_cidr]
    description = "SSH restricted to operator IP"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, { Name = "archlens-ec2-sg" })
}

# SG do RDS — aceita Postgres apenas do SG da EC2.
resource "aws_security_group" "rds" {
  name        = "archlens-ec2-rds-sg"
  description = "Allow PostgreSQL from EC2 docker-compose host"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ec2.id]
    description     = "PostgreSQL from EC2"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, { Name = "archlens-ec2-rds-sg" })
}
