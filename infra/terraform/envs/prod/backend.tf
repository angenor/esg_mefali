terraform {
  required_version = ">= 1.7"

  # Remote state PROD isolé — bucket + table DynamoDB per-env
  # (MEDIUM-10.7-5 review round 1 — isolation stricte staging/prod).
  # ⚠️ Accès IAM : uniquement rôle admin Mefali (pas CI STAGING).
  backend "s3" {
    bucket         = "mefali-terraform-state-prod"
    key            = "env/prod/terraform.tfstate"
    region         = "eu-west-3"
    dynamodb_table = "mefali-terraform-locks-prod"
    encrypt        = true
  }
}
