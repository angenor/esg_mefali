terraform {
  required_version = ">= 1.7"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.40"
    }
  }
}

resource "aws_ecs_cluster" "main" {
  name = "mefali-${var.env_name}"

  setting {
    name  = "containerInsights"
    value = "enabled" # NFR observabilité
  }

  tags = var.tags
}

resource "aws_cloudwatch_log_group" "backend" {
  name              = "/mefali/${var.env_name}/backend"
  retention_in_days = 30

  tags = var.tags
}

# Task definition Fargate — backend FastAPI
resource "aws_ecs_task_definition" "backend" {
  family                   = "mefali-${var.env_name}-backend"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.cpu
  memory                   = var.memory
  execution_role_arn       = var.execution_role_arn
  task_role_arn            = var.task_role_arn

  container_definitions = jsonencode([
    {
      name      = "backend"
      image     = var.container_image
      essential = true

      portMappings = [
        {
          containerPort = 8000
          protocol      = "tcp"
        }
      ]

      environment = [
        for k, v in var.container_env : { name = k, value = v }
      ]

      secrets = [
        for k, arn in var.container_secrets : { name = k, valueFrom = arn }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.backend.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "backend"
        }
      }

      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:8000/api/health || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    }
  ])

  tags = var.tags
}

resource "aws_ecs_service" "backend" {
  name            = "mefali-${var.env_name}-backend"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.backend.arn
  desired_count   = var.task_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.subnet_ids
    security_groups  = var.security_group_ids
    assign_public_ip = false # Private subnets + NAT
  }

  # Rolling update
  deployment_maximum_percent         = 200
  deployment_minimum_healthy_percent = 100

  deployment_circuit_breaker {
    enable   = true
    rollback = true # Auto rollback on deploy failure
  }

  tags = var.tags
}
