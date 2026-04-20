output "cluster_id" {
  description = "ECS cluster ID"
  value       = aws_ecs_cluster.main.id
}

output "cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.main.name
}

output "service_name" {
  description = "ECS service name for backend"
  value       = aws_ecs_service.backend.name
}

output "task_definition_arn" {
  description = "Task definition ARN"
  value       = aws_ecs_task_definition.backend.arn
}

output "log_group_name" {
  description = "CloudWatch log group for backend"
  value       = aws_cloudwatch_log_group.backend.name
}
