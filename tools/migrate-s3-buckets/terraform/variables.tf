variable "region" {
  description = "The region to use"
  default     = "eu-west-1"
}

variable "bucket1" {
  description = "The name of the S3 bucket to use for the production environment"
  default     = "production-s3"
}

variable "bucket2" {
  description = "The name of the S3 bucket to use for the legacy environment"
  default     = "legacy-s3"
}

variable "aws_access_key" {}

variable "aws_secret_key" {}
