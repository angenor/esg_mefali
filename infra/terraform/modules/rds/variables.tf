variable "env_name" {
  description = "Environment name (staging|prod) — NFR73 isolation"
  type        = string
  validation {
    condition     = contains(["staging", "prod"], var.env_name)
    error_message = "env_name must be one of: staging, prod (NFR73)."
  }
}

variable "aws_region" {
  description = "AWS region (UE only — NFR24 data residency)"
  type        = string
  default     = "eu-west-3"
  validation {
    # Miroir ALLOWED_EU_REGIONS Python (backend/app/core/config.py)
    condition = contains(
      [
        "eu-west-1", "eu-west-2", "eu-west-3",
        "eu-central-1", "eu-central-2",
        "eu-south-1", "eu-south-2",
        "eu-north-1",
      ],
      var.aws_region
    )
    error_message = "aws_region must be a UE region (NFR24 data residency)."
  }
}

variable "instance_class" {
  description = "RDS instance class (ex: db.t3.micro STAGING, db.t3.medium PROD)"
  type        = string
}

variable "multi_az" {
  description = "Multi-AZ deployment for HA (NFR33 backup 2 AZ — PROD only)"
  type        = bool
  default     = false
}

variable "storage_gb" {
  description = "Allocated storage in GB"
  type        = number
  default     = 20
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "esg_mefali"
}

variable "db_username" {
  description = "Master username (password from Secrets Manager — never in tfvars)"
  type        = string
  default     = "mefali_admin"
}

variable "secret_password_arn" {
  description = "ARN of Secrets Manager secret containing master password"
  type        = string
  sensitive   = true
}

variable "vpc_security_group_ids" {
  description = "VPC security groups for RDS"
  type        = list(string)
  default     = []
}

variable "subnet_ids" {
  description = "Subnet IDs for RDS DB subnet group"
  type        = list(string)
  default     = []
}

variable "backup_retention_days" {
  description = "Backup retention period (NFR34 RTO 4h / NFR35 RPO 24h — 7 days MVP)"
  type        = number
  default     = 7
}

variable "tags" {
  description = "Standard tags propagated from env caller"
  type        = map(string)
  default     = {}
}
