variable "aws_region" {
  type        = string
  description = "AWS region for SageMaker resources"
  default     = "us-east-1"
}

variable "artifact_bucket_name" {
  type        = string
  description = "S3 bucket for model and pipeline artifacts"
}

variable "sagemaker_domain_name" {
  type        = string
  description = "Name of the SageMaker Studio domain"
}

variable "sagemaker_execution_role_arn" {
  type        = string
  description = "IAM role ARN used by SageMaker"
}

variable "vpc_id" {
  type        = string
  description = "VPC id for SageMaker domain"
}

variable "private_subnet_ids" {
  type        = list(string)
  description = "Private subnet ids used by SageMaker"
}
