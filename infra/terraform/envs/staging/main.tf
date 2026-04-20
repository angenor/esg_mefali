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

# Provider alias pour replication destination (pas utilisé en STAGING — CRR off)
provider "aws" {
  alias  = "replica"
  region = "eu-west-1"
  default_tags {
    tags = local.standard_tags
  }
}

locals {
  env_name = "staging"

  standard_tags = {
    Environment = local.env_name
    Project     = "mefali"
    ManagedBy   = "terraform"
  }
}

# S3 — bucket STAGING, pas de CRR (budget NFR69 ~50 €/mois)
module "s3" {
  source = "../../modules/s3"

  env_name    = local.env_name
  aws_region  = var.aws_region
  bucket_name = "mefali-${local.env_name}"

  # STAGING : CRR OFF pour limiter coût (PROD only)
  crr_destination_bucket = null

  tags = local.standard_tags

  providers = {
    aws         = aws
    aws.replica = aws.replica
  }
}

# IAM — 2 rôles (app, admin) + execution — AC4 granulaire
module "iam" {
  source = "../../modules/iam"

  env_name                  = local.env_name
  s3_bucket_name            = module.s3.bucket_name
  secrets_manager_namespace = "mefali/${local.env_name}"

  tags = local.standard_tags
}

# RDS — t3.micro single-AZ (STAGING budget)
module "rds" {
  source = "../../modules/rds"

  env_name                = local.env_name
  aws_region              = var.aws_region
  instance_class          = "db.t3.micro"
  multi_az                = false
  storage_gb              = 20
  secret_password_arn     = var.rds_secret_password_arn
  subnet_ids              = var.subnet_ids
  vpc_security_group_ids  = var.rds_security_group_ids
  backup_retention_days   = 7

  tags = local.standard_tags
}

# ECS — 1 task Fargate 512 CPU / 1024 MB
module "ecs" {
  source = "../../modules/ecs"

  env_name           = local.env_name
  aws_region         = var.aws_region
  container_image    = var.container_image
  task_count         = 1
  cpu                = 512
  memory             = 1024
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
