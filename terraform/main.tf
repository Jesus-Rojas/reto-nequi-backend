terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Opcional: descomenta para guardar el estado en S3
  # backend "s3" {
  #   bucket         = "tu-bucket-terraform-state"
  #   key            = "reto-nequi/backend/terraform.tfstate"
  #   region         = "us-east-1"
  #   dynamodb_table = "terraform-lock"
  #   encrypt        = true
  # }
}

locals {
  localstack_endpoint = "http://localhost:4566"
}

provider "aws" {
  region = var.aws_region

  # ── LocalStack (desarrollo local) ────────────────────────────────────────
  # Cuando use_localstack = true se usan credenciales ficticias y todos los
  # endpoints apuntan al contenedor LocalStack en lugar de a AWS real.
  dynamic "endpoints" {
    for_each = var.use_localstack ? [1] : []
    content {
      ec2            = local.localstack_endpoint
      iam            = local.localstack_endpoint
      sts            = local.localstack_endpoint
      s3             = local.localstack_endpoint
      secretsmanager = local.localstack_endpoint
      ssm            = local.localstack_endpoint
    }
  }

  access_key                  = var.use_localstack ? "test" : null
  secret_key                  = var.use_localstack ? "test" : null
  skip_credentials_validation = var.use_localstack
  skip_metadata_api_check     = var.use_localstack
  skip_requesting_account_id  = var.use_localstack

  default_tags {
    tags = {
      Project     = var.project_name
      Component   = "backend"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}
