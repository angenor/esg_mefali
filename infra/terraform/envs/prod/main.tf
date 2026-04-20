terraform {
  required_version = ">= 1.7"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.40"
    }
  }
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = local.standard_tags
  }
}

# Provider alias EU-West-1 pour bucket destination CRR (NFR33 backup 2 AZ)
provider "aws" {
  alias  = "replica"
  region = var.crr_destination_region
  default_tags {
    tags = local.standard_tags
  }
}

locals {
  env_name = "prod"

  standard_tags = {
    Environment = local.env_name
    Project     = "mefali"
    ManagedBy   = "terraform"
  }
}

# S3 — bucket PROD avec CRR EU-West-3 → EU-West-1 (AC6 + NFR33)
module "s3" {
  source = "../../modules/s3"

  env_name    = local.env_name
  aws_region  = var.aws_region
  bucket_name = "mefali-${local.env_name}"

  crr_destination_bucket = "mefali-${local.env_name}-backup-${var.crr_destination_region}"
  crr_destination_region = var.crr_destination_region

  tags = local.standard_tags

  providers = {
    aws         = aws
    aws.replica = aws.replica
  }
}

# IAM — 2 rôles (app, admin avec MFA) — AC4
module "iam" {
  source = "../../modules/iam"

  env_name                  = local.env_name
  s3_bucket_name            = module.s3.bucket_name
  secrets_manager_namespace = "mefali/${local.env_name}"

  tags = local.standard_tags
}

# RDS — t3.medium multi-AZ (PROD HA)
module "rds" {
  source = "../../modules/rds"

  env_name                = local.env_name
  aws_region              = var.aws_region
  instance_class          = "db.t3.medium"
  multi_az                = true # NFR33 backup 2 AZ
  storage_gb              = 100
  secret_password_arn     = var.rds_secret_password_arn
  subnet_ids              = var.subnet_ids
  vpc_security_group_ids  = var.rds_security_group_ids
  backup_retention_days   = 7 # NFR34 RTO 4h

  tags = local.standard_tags
}

# ECS — 2 tasks Fargate 1024 CPU / 2048 MB (HA rolling deploy)
module "ecs" {
  source = "../../modules/ecs"

  env_name           = local.env_name
  aws_region         = var.aws_region
  container_image    = var.container_image
  task_count         = 2
  cpu                = 1024
  memory             = 2048
  execution_role_arn = module.iam.execution_role_arn
  task_role_arn      = module.iam.app_role_arn
  subnet_ids         = var.subnet_ids
  security_group_ids = var.ecs_security_group_ids

  container_env = {
    ENV_NAME                        = local.env_name
    STORAGE_PROVIDER                = "s3"
    AWS_S3_BUCKET                   = module.s3.bucket_name
    AWS_REGION                      = var.aws_region
    AWS_SECRETS_MANAGER_NAMESPACE   = "mefali/${local.env_name}"
    DEBUG                           = "false"
  }

  tags = local.standard_tags
}
