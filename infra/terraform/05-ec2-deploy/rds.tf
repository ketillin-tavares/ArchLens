# RDS PostgreSQL para o stack EC2.
# Cria apenas a instancia + database inicial 'archlens'. Os 4 databases
# de servico (upload_db, processing_db, report_db, litellm_db) e seus
# users sao criados pelo bootstrap-rds.sh na primeira boot da EC2.

module "rds" {
  source  = "terraform-aws-modules/rds/aws"
  version = "6.5.2"

  identifier        = "archlens-ec2-db"
  engine            = "postgres"
  engine_version    = var.rds_engine_version
  family            = "postgres${split(".", var.rds_engine_version)[0]}"
  instance_class    = var.rds_instance_class
  allocated_storage = var.rds_allocated_storage

  db_name  = "archlens"
  username = "archlens"
  password = var.db_master_password
  port     = 5432

  manage_master_user_password = false

  vpc_security_group_ids = [aws_security_group.rds.id]
  create_db_subnet_group = true
  subnet_ids             = module.vpc.private_subnets

  multi_az                = false
  skip_final_snapshot     = true
  deletion_protection     = false
  backup_retention_period = 1

  performance_insights_enabled    = true
  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]

  tags = local.common_tags
}
