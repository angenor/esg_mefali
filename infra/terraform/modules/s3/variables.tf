variable "env_name" {
  description = "Environment name (staging|prod) — NFR73 isolation"
  type        = string
  validation {
    condition     = contains(["staging", "prod"], var.env_name)
    error_message = "env_name must be one of: staging, prod."
  }
}

variable "aws_region" {
  description = "AWS region — NFR24 UE data residency"
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

variable "bucket_name" {
  description = "S3 bucket name (ex: mefali-prod)"
  type        = string
}

variable "crr_destination_bucket" {
  description = "CRR destination bucket name in EU-West-1 (null = CRR disabled)"
  type        = string
  default     = null
}

variable "crr_destination_region" {
  description = "CRR destination region (NFR33 2 AZ — default EU-West-1)"
  type        = string
  default     = "eu-west-1"
  validation {
    condition = contains(
      [
        "eu-west-1", "eu-west-2",
        "eu-central-1", "eu-central-2",
        "eu-south-1", "eu-south-2",
        "eu-north-1",
      ],
      var.crr_destination_region
    )
    error_message = "CRR destination must be a UE region != source (NFR24 + NFR33)."
  }
}

variable "noncurrent_version_retention_days" {
  description = "Retention for noncurrent versions (NFR69 budget control)"
  type        = number
  default     = 30
}

variable "tags" {
  description = "Standard tags"
  type        = map(string)
  default     = {}
}
