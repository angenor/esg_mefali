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

variable "container_image" {
  description = "Backend image URI (ex: ghcr.io/mefali/backend:sha-abc123)"
  type        = string
}

variable "task_count" {
  description = "Desired task count (1 STAGING, 2+ PROD)"
  type        = number
  default     = 1
}

variable "cpu" {
  description = "Task CPU units (512 STAGING, 1024 PROD)"
  type        = number
  default     = 512
}

variable "memory" {
  description = "Task memory MB (1024 STAGING, 2048 PROD)"
  type        = number
  default     = 1024
}

variable "execution_role_arn" {
  description = "ECS execution role ARN (from iam module)"
  type        = string
}

variable "task_role_arn" {
  description = "ECS task role ARN (app role, from iam module)"
  type        = string
}

variable "subnet_ids" {
  description = "Subnet IDs for Fargate tasks"
  type        = list(string)
  default     = []
}

variable "security_group_ids" {
  description = "Security groups for Fargate tasks"
  type        = list(string)
  default     = []
}

variable "container_env" {
  description = "Env vars for backend container (ENV_NAME, etc.)"
  type        = map(string)
  default     = {}
}

variable "container_secrets" {
  description = "Secret references from Secrets Manager (name → secret ARN)"
  type        = map(string)
  default     = {}
}

variable "tags" {
  description = "Standard tags"
  type        = map(string)
  default     = {}
}
