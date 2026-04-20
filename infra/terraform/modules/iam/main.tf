terraform {
  required_version = ">= 1.7"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.40"
    }
  }
}

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

locals {
  account_id = data.aws_caller_identity.current.account_id
  region     = data.aws_region.current.name

  # Scope STRICT per-env — jamais de wildcard (absorption LOW-10.6-2)
  bucket_arn        = "arn:aws:s3:::${var.s3_bucket_name}"
  bucket_objects    = "${local.bucket_arn}/*"
  secrets_namespace = "arn:aws:secretsmanager:${local.region}:${local.account_id}:secret:${var.secrets_manager_namespace}/*"
}

# -----------------------------------------------------------------------------
# Rôle 1 — APP (ECS Fargate task role) — PAS DE DeleteObject (AC4)
# -----------------------------------------------------------------------------
# Le backend fait du soft-delete applicatif via Document.deleted_at (migration
# 027 RLS). L'action AWS Delete reste réservée au rôle admin avec MFA.

resource "aws_iam_role" "app" {
  name = "mefali-${var.env_name}-app"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = var.tags
}

resource "aws_iam_policy" "app_s3_read_write" {
  name = "mefali-${var.env_name}-app-s3-read-write"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ReadWriteOwnBucket"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket",
        ]
        # Scope STRICT — bucket + objets du bucket, anti-wildcard
        Resource = [
          local.bucket_arn,     # Pour ListBucket
          local.bucket_objects, # Pour Get/Put
        ]
        # JAMAIS DeleteObject ici — AC4 absorption LOW-10.6-2
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "app_s3" {
  role       = aws_iam_role.app.name
  policy_arn = aws_iam_policy.app_s3_read_write.arn
}

resource "aws_iam_policy" "app_secrets_read" {
  name = "mefali-${var.env_name}-app-secrets-read"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ReadOwnNamespaceSecrets"
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret",
        ]
        # Scope STRICT namespace per-env (mefali/prod/*) — pas d'accès mefali/staging/*
        Resource = local.secrets_namespace
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "app_secrets" {
  role       = aws_iam_role.app.name
  policy_arn = aws_iam_policy.app_secrets_read.arn
}

# ECS execution role (pull image ECR, logs CloudWatch) — distinct task role
resource "aws_iam_role" "execution" {
  name = "mefali-${var.env_name}-execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "execution_ecs_default" {
  role       = aws_iam_role.execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# -----------------------------------------------------------------------------
# Rôle 2 — ADMIN (assumé par IAM user humain avec MFA) — Delete + MFA required
# -----------------------------------------------------------------------------

resource "aws_iam_role" "admin" {
  name = "mefali-${var.env_name}-admin"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          # Root account — IAM users doivent assume-role avec MFA pour utiliser
          AWS = "arn:aws:iam::${local.account_id}:root"
        }
        Action = "sts:AssumeRole"
        Condition = {
          Bool = {
            # Assumption du rôle admin nécessite MFA récent (anti-automation)
            "aws:MultiFactorAuthPresent" = "true"
          }
        }
      }
    ]
  })

  tags = var.tags
}

resource "aws_iam_policy" "admin_s3_delete_mfa" {
  name = "mefali-${var.env_name}-admin-s3-delete-mfa"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "DeleteOwnBucketWithMFA"
        Effect = "Allow"
        Action = [
          "s3:DeleteObject",
          "s3:DeleteObjectVersion",
        ]
        # Scope STRICT bucket per-env — pas de wildcard (AC4)
        Resource = local.bucket_objects
        Condition = {
          Bool = {
            # Défense profondeur : même si le rôle est assumé par erreur,
            # l'action Delete n'est autorisée qu'avec MFA présent.
            "aws:MultiFactorAuthPresent" = "true"
          }
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "admin_s3_delete" {
  role       = aws_iam_role.admin.name
  policy_arn = aws_iam_policy.admin_s3_delete_mfa.arn
}
