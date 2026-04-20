terraform {
  required_version = ">= 1.7"
  required_providers {
    aws = {
      source                = "hashicorp/aws"
      version               = ">= 5.40"
      configuration_aliases = [aws.replica]
    }
  }
}

# Bucket source (env region, typiquement eu-west-3)
resource "aws_s3_bucket" "main" {
  bucket = var.bucket_name

  tags = merge(
    var.tags,
    {
      Name = var.bucket_name
    }
  )
}

# NFR25 — chiffrement at rest SSE-S3 AES256 (pas KMS MVP, différé Phase Growth)
resource "aws_s3_bucket_server_side_encryption_configuration" "main" {
  bucket = aws_s3_bucket.main.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block public access (défense profondeur — aucun bucket Mefali public)
resource "aws_s3_bucket_public_access_block" "main" {
  bucket = aws_s3_bucket.main.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Versioning — prérequis CRR (AC6), protection anti-suppression accidentelle
resource "aws_s3_bucket_versioning" "main" {
  bucket = aws_s3_bucket.main.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Lifecycle — expire noncurrent versions après N jours (NFR69 budget)
resource "aws_s3_bucket_lifecycle_configuration" "main" {
  depends_on = [aws_s3_bucket_versioning.main]

  bucket = aws_s3_bucket.main.id

  rule {
    id     = "expire-noncurrent-versions"
    status = "Enabled"

    filter {}

    noncurrent_version_expiration {
      noncurrent_days = var.noncurrent_version_retention_days
    }
  }
}

# -----------------------------------------------------------------------------
# CRR (AC6) — activé conditionnellement via var.crr_destination_bucket != null
# Ordre strict AWS : Versioning MUST be enabled before Replication Configuration.
# -----------------------------------------------------------------------------

# Bucket destination EU-West-1 (créé uniquement si CRR demandée)
resource "aws_s3_bucket" "destination" {
  count    = var.crr_destination_bucket != null ? 1 : 0
  provider = aws.replica

  bucket = var.crr_destination_bucket

  tags = merge(
    var.tags,
    {
      Name    = var.crr_destination_bucket
      Purpose = "crr-destination"
    }
  )
}

resource "aws_s3_bucket_server_side_encryption_configuration" "destination" {
  count    = var.crr_destination_bucket != null ? 1 : 0
  provider = aws.replica

  bucket = aws_s3_bucket.destination[0].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_versioning" "destination" {
  count    = var.crr_destination_bucket != null ? 1 : 0
  provider = aws.replica

  bucket = aws_s3_bucket.destination[0].id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "destination" {
  count    = var.crr_destination_bucket != null ? 1 : 0
  provider = aws.replica

  bucket = aws_s3_bucket.destination[0].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# IAM role pour CRR — assumé par S3 service (pas humain)
data "aws_caller_identity" "current" {}

resource "aws_iam_role" "replication" {
  count = var.crr_destination_bucket != null ? 1 : 0

  name = "mefali-${var.env_name}-s3-replication"

  # Anti confused deputy (MEDIUM-10.7-2 review round 1) — verrouille l'assume
  # au seul compte + bucket source pour éviter qu'un autre compte AWS avec
  # accès S3 service principal puisse assumer ce rôle.
  # Ref : https://docs.aws.amazon.com/IAM/latest/UserGuide/confused-deputy.html
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "s3.amazonaws.com"
        }
        Action = "sts:AssumeRole"
        Condition = {
          StringEquals = {
            "aws:SourceAccount" = data.aws_caller_identity.current.account_id
          }
          ArnLike = {
            "aws:SourceArn" = aws_s3_bucket.main.arn
          }
        }
      }
    ]
  })

  tags = var.tags
}

resource "aws_iam_policy" "replication" {
  count = var.crr_destination_bucket != null ? 1 : 0

  name = "mefali-${var.env_name}-s3-replication"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowSourceBucketReplicationRead"
        Effect = "Allow"
        Action = [
          "s3:GetReplicationConfiguration",
          "s3:ListBucket",
          "s3:GetObjectVersionForReplication",
          "s3:GetObjectVersionAcl",
          "s3:GetObjectVersionTagging",
        ]
        # Scope STRICT source bucket (anti-wildcard AC4)
        Resource = [
          aws_s3_bucket.main.arn,
          "${aws_s3_bucket.main.arn}/*",
        ]
      },
      {
        Sid    = "AllowDestinationBucketReplicationWrite"
        Effect = "Allow"
        Action = [
          "s3:ReplicateObject",
          "s3:ReplicateDelete",
          "s3:ReplicateTags",
        ]
        # Scope STRICT destination bucket (anti-wildcard AC4)
        Resource = "${aws_s3_bucket.destination[0].arn}/*"
      },
    ]
  })
}

resource "aws_iam_role_policy_attachment" "replication" {
  count = var.crr_destination_bucket != null ? 1 : 0

  role       = aws_iam_role.replication[0].name
  policy_arn = aws_iam_policy.replication[0].arn
}

# Replication configuration — ORDRE CRITIQUE depends_on
resource "aws_s3_bucket_replication_configuration" "main" {
  count = var.crr_destination_bucket != null ? 1 : 0

  # ⚠️ ORDRE OBLIGATOIRE : Versioning source + destination AVANT Replication
  # + policy attachment AVANT replication (MEDIUM-10.7-1 review round 1 — évite
  # race Terraform où S3 replication config est créée avant que le rôle ait
  # la policy attachée → AccessDenied sur premier replicate).
  depends_on = [
    aws_s3_bucket_versioning.main,
    aws_s3_bucket_versioning.destination,
    aws_iam_role_policy_attachment.replication,
  ]

  role   = aws_iam_role.replication[0].arn
  bucket = aws_s3_bucket.main.id

  rule {
    id     = "replicate-all-${var.aws_region}-to-${var.crr_destination_region}"
    status = "Enabled"

    filter {}

    destination {
      bucket        = aws_s3_bucket.destination[0].arn
      storage_class = "STANDARD_IA" # Coût réduit backup froid

      encryption_configuration {
        # SSE-S3 AES256 replica (aligné Story 10.6 NFR25)
        # null = pas de KMS override, utilise SSE-S3 par défaut du bucket dest
        replica_kms_key_id = null
      }
    }

    # Anti-accidentel : suppression PROD ne propage PAS vers EU-West-1
    delete_marker_replication {
      status = "Disabled"
    }
  }
}
