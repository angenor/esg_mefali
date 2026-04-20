variable "aws_region" {
  description = "AWS region PROD (NFR24 UE — default eu-west-3)"
  type        = string
  default     = "eu-west-3"
  validation {
    condition = contains(
      [
        "eu-west-1", "eu-west-2", "eu-west-3",
        "eu-central-1", "eu-central-2",
        "eu-south-1", "eu-south-2",
        "eu-north-1",
      ],
      var.aws_region
    )
    error_message = "aws_region must be a UE region (NFR24)."
  }
}

variable "crr_destination_region" {
  description = "CRR destination region — NFR33 backup 2 AZ (default eu-west-1)"
  type        = string
  default     = "eu-west-1"
}

variable "container_image" {
  description = "Backend image URI (ghcr.io/mefali/backend:sha-xxx)"
  type        = string
}

variable "rds_secret_password_arn" {
  description = "ARN of Secrets Manager secret containing RDS master password"
  type        = string
  sensitive   = true
}

variable "subnet_ids" {
  description = "Private subnets for RDS + ECS (multi-AZ PROD)"
  type        = list(string)
}

variable "rds_security_group_ids" {
  description = "Security groups for RDS"
  type        = list(string)
}

variable "ecs_security_group_ids" {
  description = "Security groups for ECS tasks"
  type        = list(string)
}
