variable "env_name" {
  description = "Environment name (staging|prod) — NFR73 isolation"
  type        = string
  validation {
    condition     = contains(["staging", "prod"], var.env_name)
    error_message = "env_name must be one of: staging, prod."
  }
}

variable "s3_bucket_name" {
  description = "S3 bucket name (output from s3 module — ex: mefali-prod)"
  type        = string
}

variable "secrets_manager_namespace" {
  description = "Secrets Manager namespace (ex: mefali/prod)"
  type        = string
}

variable "tags" {
  description = "Standard tags"
  type        = map(string)
  default     = {}
}
