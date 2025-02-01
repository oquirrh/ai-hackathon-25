
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

# Configure the AWS Provider for LocalStack Testing
provider "aws" {
  region                      = "us-west-2"
  access_key                  = "test"  # Dummy credentials for LocalStack
  secret_key                  = "test"
  skip_credentials_validation = true
  skip_requesting_account_id  = true
  skip_metadata_api_check     = true

  endpoints {
    ec2 = "http://localhost:4566"
    s3  = "http://localhost:4566"
    elasticbeanstalk = "http://localhost:4566"
    iam = "http://localhost:4566"
    route53 = "http://localhost:4566"
    apigateway = "http://localhost:4566"
    cloudfront = "http://localhost:4566"
    cloudwatch = "http://localhost:4566"
    elb = "http://localhost:4566"
    lambda = "http://localhost:4566"
  }

  # Force S3 to use path-style addressing for LocalStack compatibility
  s3_force_path_style = true
}

##############################
# Resource Definitions Start #
##############################

# S3 Bucket for Application Code
resource "aws_s3_bucket" "beanstalk_app_bucket" {
  bucket = "elastic-beanstalk-app-bucket" # Replace with your desired bucket name
  acl    = "private"

  versioning {
    enabled = true
  }

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }
}

# IAM Role for Elastic Beanstalk
resource "aws_iam_role" "aws_elasticbeanstalk_service_role" {
  name = "aws-elasticbeanstalk-service-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Principal = {
          Service = "elasticbeanstalk.amazonaws.com"
        }
        Effect = "Allow"
        Sid    = ""
      },
    ]
  })
}

# IAM Role Policy Attachment for Elastic Beanstalk Service Role
resource "aws_iam_role_policy_attachment" "aws_elasticbeanstalk_service_policy" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSElasticBeanstalkService"
  role       = aws_iam_role.aws_elasticbeanstalk_service_role.name
}

# IAM Instance Profile for EC2 Instances in Elastic Beanstalk
resource "aws_iam_instance_profile" "aws_elasticbeanstalk_ec2_role" {
  name = "aws-elasticbeanstalk-ec2-role"
  role = aws_iam_role.aws_elasticbeanstalk_ec2_role.name
}

# IAM Role for EC2 Instances in Elastic Beanstalk
resource "aws_iam_role" "aws_elasticbeanstalk_ec2_role" {
  name = "aws-elasticbeanstalk-ec2-instance-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
        Effect = "Allow"
        Sid    = ""
      },
    ]
  })
}

# IAM Role Policy Attachment for Elastic Beanstalk EC2 Role - WebTier
resource "aws_iam_role_policy_attachment" "aws_elasticbeanstalk_ec2_policy_webtier" {
  policy_arn = "arn:aws:iam::aws:policy/AWSElasticBeanstalkWebTier"
  role       = aws_iam_role.aws_elasticbeanstalk_ec2_role.name
}

# IAM Role Policy Attachment for Elastic Beanstalk EC2 Role - WorkerTier (if needed, for web tier, we might not need worker tier policy)
resource "aws_iam_role_policy_attachment" "aws_elasticbeanstalk_ec2_policy_workertier" {
  policy_arn = "arn:aws:iam::aws:policy/AWSElasticBeanstalkWorkerTier"
  role       = aws_iam_role.aws_elasticbeanstalk_ec2_role.name
}

# IAM Role Policy Attachment for S3 access for EB EC2 instances
resource "aws_iam_role_policy_attachment" "aws_elasticbeanstalk_ec2_policy_s3" {
  policy_arn = aws_iam_policy.example_ec2_policy.arn # Reusing the S3 policy from template
  role       = aws_iam_role.aws_elasticbeanstalk_ec2_role.name
}

# IAM Policy for EC2 Instances (S3 Access) - Reusing from template, but could be refined for EB
resource "aws_iam_policy" "example_ec2_policy" {
  name        = "elastic-beanstalk-s3-access-policy"
  description = "Policy for Elastic Beanstalk EC2 instances to access S3 bucket"
  policy      = jsonencode({
    Version   = "2012-10-17",
    Statement = [{
      Action   = "s3:PutObject" # Adjust permissions as needed for EB application
      Effect   = "Allow"
      Resource = "${aws_s3_bucket.beanstalk_app_bucket.arn}/*"
      },
      {
      Action = [
        "s3:GetObject",
        "s3:ListBucket"
      ]
      Effect   = "Allow"
      Resource = [
        "${aws_s3_bucket.beanstalk_app_bucket.arn}",
        "${aws_s3_bucket.beanstalk_app_bucket.arn}/*"
      ]
    }]
  })
}


# Elastic Beanstalk Application
resource "aws_elastic_beanstalk_application" "nestjs_app" {
  name        = "nestjs-app"
  description = "Elastic Beanstalk application for NestJS"
}

# Elastic Beanstalk Environment
resource "aws_elastic_beanstalk_environment" "nestjs_env" {
  name          = "nestjs-env"
  application   = aws_elastic_beanstalk_application.nestjs_app.name
  solution_stack_name = "64bit Amazon Linux 2 v3.6.1 Node.js 16 running on Tomcat 8.5.57" # Or a more recent Node.js stack

  setting {
    namespace = "aws:autoscaling:launchconfiguration"
    name      = "IamInstanceProfile"
    value     = aws_iam_instance_profile.aws_elasticbeanstalk_ec2_role.name
  }

  setting {
    namespace = "aws:elasticbeanstalk:environment"
    name      = "ServiceRole"
    value     = aws_iam_role.aws_elasticbeanstalk_service_role.name
  }
}

# Route 53 Hosted Zone (Assuming you have a domain - replace example.com)
resource "aws_route53_zone" "primary" {
  name = "example.com" # Replace with your domain
}

# Route 53 Record to point to Elastic Beanstalk Environment (CNAME)
resource "aws_route53_record" "app_dns" {
  zone_id = aws_route53_zone.primary.zone_id
  name    = "hello.example.com" # Replace with your subdomain
  type    = "CNAME"
  ttl     = "300"
  records = [aws_elastic_beanstalk_environment.nestjs_env.endpoint_url] # Use the EB environment endpoint
}
