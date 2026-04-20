output "app_role_arn" {
  description = "ARN du rôle app (ECS task role, pas de Delete S3)"
  value       = aws_iam_role.app.arn
}

output "app_role_name" {
  description = "Nom du rôle app"
  value       = aws_iam_role.app.name
}

output "execution_role_arn" {
  description = "ARN du rôle exécution ECS (pull image ECR, logs CloudWatch)"
  value       = aws_iam_role.execution.arn
}

output "admin_role_arn" {
  description = "ARN du rôle admin (assumé par IAM user avec MFA)"
  value       = aws_iam_role.admin.arn
}

output "app_policy_app_s3_read_write_name" {
  description = "Nom policy S3 app (pour tests anti-wildcard)"
  value       = aws_iam_policy.app_s3_read_write.name
}

output "admin_policy_s3_delete_mfa_name" {
  description = "Nom policy S3 admin (pour tests MFA condition)"
  value       = aws_iam_policy.admin_s3_delete_mfa.name
}
