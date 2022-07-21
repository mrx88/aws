provider "aws" {
  access_key = var.aws_access_key
  secret_key = var.aws_secret_key
  region     = var.region
}


resource "aws_s3_bucket" "bucket1" {
  bucket = var.bucket1
}

resource "aws_s3_bucket" "bucket2" {
  bucket = var.bucket2
}

resource "aws_s3_bucket_acl" "bucket1" {
  bucket = aws_s3_bucket.bucket1.id
  acl    = "private"
}

resource "aws_s3_bucket_acl" "bucket2" {
  bucket = aws_s3_bucket.bucket2.id
  acl    = "private"
}