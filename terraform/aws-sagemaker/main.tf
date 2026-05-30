terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.47"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

resource "aws_s3_bucket" "ml_artifacts" {
  bucket = var.artifact_bucket_name
}

resource "aws_sagemaker_domain" "studio" {
  domain_name = var.sagemaker_domain_name
  auth_mode   = "IAM"

  default_user_settings {
    execution_role = var.sagemaker_execution_role_arn
  }

  vpc_id     = var.vpc_id
  subnet_ids = var.private_subnet_ids
}
