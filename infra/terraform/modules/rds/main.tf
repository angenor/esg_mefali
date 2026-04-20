terraform {
  required_version = ">= 1.7"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.40"
    }
  }
}

# Lecture dynamique du password depuis Secrets Manager — jamais de secret
# plaintext dans Terraform state (limite blast radius si state leak).
data "aws_secretsmanager_secret_version" "db_password" {
  secret_id = var.secret_password_arn
}

resource "aws_db_subnet_group" "main" {
  name       = "mefali-${var.env_name}-rds-subnet-group"
  subnet_ids = var.subnet_ids
  tags       = var.tags
}

resource "aws_db_instance" "main" {
  identifier = "mefali-${var.env_name}"

  engine         = "postgres"
  engine_version = "16.4"
  instance_class = var.instance_class

  allocated_storage     = var.storage_gb
  storage_type          = "gp3"
  storage_encrypted     = true # NFR25 chiffrement at rest

  db_name  = var.db_name
  username = var.db_username
  password = data.aws_secretsmanager_secret_version.db_password.secret_string

  multi_az               = var.multi_az # NFR33 backup 2 AZ (PROD only)
  vpc_security_group_ids = var.vpc_security_group_ids
  db_subnet_group_name   = aws_db_subnet_group.main.name
  publicly_accessible    = false # Toujours private subnet

  # NFR34 RTO 4h / NFR35 RPO 24h
  backup_retention_period = var.backup_retention_days
  backup_window           = "02:00-03:00" # UTC — window low-traffic
  maintenance_window      = "sun:03:00-sun:04:00"
  deletion_protection     = var.env_name == "prod" # PROD protégé suppression accidentelle
  skip_final_snapshot     = var.env_name != "prod"

  # Performance insights pour observabilité (NFR perf)
  performance_insights_enabled = true

  # Auto minor version upgrade (security patches)
  auto_minor_version_upgrade = true

  tags = merge(
    var.tags,
    {
      Name = "mefali-${var.env_name}-rds"
    }
  )
}
