module "rds" {
  source  = "terraform-aws-modules/rds/aws"
  version = "6.5.2"

  identifier        = "archlens-db"
  engine            = "postgres"
  engine_version    = var.rds_engine_version
  family            = "postgres${split(".", var.rds_engine_version)[0]}"
  instance_class    = var.rds_instance_class
  allocated_storage = var.rds_allocated_storage

  db_name  = "archlens" # database inicial
  username = "archlens"
  password = var.db_password
  port     = 5432

  vpc_security_group_ids = [aws_security_group.rds.id]
  create_db_subnet_group = true
  subnet_ids             = module.vpc.private_subnets

  # Os outros 3 databases (upload_db, processing_db, report_db) são
  # criados via migrations Alembic dos próprios serviços na primeira
  # inicialização, não pelo Terraform.

  multi_az                = false # economizar
  skip_final_snapshot     = true  # dev/hackathon only
  deletion_protection     = false # dev/hackathon only
  backup_retention_period = 1

  # Performance Insights (free tier)
  performance_insights_enabled = true

  # Logs exportados para CloudWatch (observabilidade)
  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]

  tags = local.common_tags
}
