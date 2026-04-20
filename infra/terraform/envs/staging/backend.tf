terraform {
  required_version = ">= 1.7"

  # Remote state STAGING isolé — bucket + table DynamoDB per-env
  # (MEDIUM-10.7-5 review round 1 — évite qu'un rôle CI staging compromis
  # puisse lire le state PROD via le même bucket S3).
  # Bootstrap manuel des deux buckets documenté dans infra/terraform/README.md.
  backend "s3" {
    bucket         = "mefali-terraform-state-staging"
    key            = "env/staging/terraform.tfstate"
    region         = "eu-west-3"
    dynamodb_table = "mefali-terraform-locks-staging"
    encrypt        = true
  }
}
