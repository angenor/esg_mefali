output "bucket_name" {
  description = "Source bucket name"
  value       = aws_s3_bucket.main.bucket
}

output "bucket_arn" {
  description = "Source bucket ARN"
  value       = aws_s3_bucket.main.arn
}

output "bucket_id" {
  description = "Source bucket ID"
  value       = aws_s3_bucket.main.id
}

output "destination_bucket_arn" {
  description = "CRR destination bucket ARN (null if CRR disabled)"
  value       = length(aws_s3_bucket.destination) > 0 ? aws_s3_bucket.destination[0].arn : null
}

output "replication_role_arn" {
  description = "IAM role ARN for S3 replication"
  value       = length(aws_iam_role.replication) > 0 ? aws_iam_role.replication[0].arn : null
}
