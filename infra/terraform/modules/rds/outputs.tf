output "db_instance_id" {
  description = "RDS instance identifier"
  value       = aws_db_instance.main.id
}

output "db_endpoint" {
  description = "RDS endpoint (hostname:port)"
  value       = aws_db_instance.main.endpoint
  sensitive   = true
}

output "db_arn" {
  description = "RDS instance ARN"
  value       = aws_db_instance.main.arn
}

output "db_subnet_group_name" {
  description = "DB subnet group name"
  value       = aws_db_subnet_group.main.name
}
