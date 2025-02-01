import os
import json
import re

from pinecone import Pinecone
import requests
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import ollama

from python_terraform import Terraform

# Load environment variables from .env file
load_dotenv()

# Constants
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX = os.getenv("PINECONE_INDEX")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = "meta-llama/llama-3.2-1b-instruct:free"  # Free model
TEMPLATE_MODEL = "google/gemini-2.0-flash-thinking-exp-1219:free"

# Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX)

# Load Embedding Model
embed_model = SentenceTransformer("all-MiniLM-L6-v2")


class TerraformAgent:

    def __init__(self):
        return

    def read_aws_services(self, file_path="aws_services_required.txt"):
        """Reads extracted AWS services from file."""
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def query_pinecone(self, services):
        """Queries Pinecone to find relevant Terraform modules for cost-effective deployment."""
        query_vector = embed_model.encode(" ".join(services)).tolist()
        response = index.query(vector=query_vector, top_k=5, include_metadata=True)
        return [match["metadata"]["text"] for match in response["matches"]]

    def query_openrouter(self, prompt, model):
        """Queries OpenRouter LLM."""
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
        }
        response = requests.post(url, headers=headers, json=data)
        return (
            response.json()
            .get("choices", [{}])[0]
            .get("message", {})
            .get("content", "No response")
        )

    def query_ollama(self, prompt, model):
        """Queries OpenRouter LLM."""
        response = ollama.chat(
            model=model, messages=[{"role": "user", "content": prompt}]
        )
        getattr(getattr(response, "message", "No response"), "content", "No response")

    def optimize_aws_services(self, aws_services, terraform_docs):
        """Uses OpenRouter LLM to determine the most cost-effective AWS services needed for deployment."""
        prompt = f"""
        Given the following AWS services:
        {aws_services}
        And the following Terraform documentation:
        {terraform_docs}
        Select only the most cost-effective and necessary AWS services to deploy this application. Also, leave out RDS, as
        our resources cannot deploy RDS. When using S3, make sure to add 's3_force_path_style = true'
        Provide justification for each selection. Ensure that all endpoints are configured to use localstack only.
        """
        return self.query_openrouter(prompt, OPENROUTER_MODEL)

    def deploy_terraform(self, working_dir="../"):
        tf = Terraform(working_dir=working_dir)

        return_code, stdout, stderr = tf.init()
        print(stdout)

        return_code, stdout, stderr = tf.apply(skip_plan=True, auto_approve=True)
        print(stdout)

    def generate_terraform_code(self, optimized_services, terraform_docs):
        """Uses OpenRouter LLM to generate a ready-to-deploy Terraform script."""
        template = """
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
        # Add additional endpoints as necessary, e.g., rds, iam, etc.
        iam = "http://localhost:4566"
      }
      
      # Force S3 to use path-style addressing for LocalStack compatibility
      s3_force_path_style = true
    }
    
    ##############################
    # Resource Definitions Start #
    ##############################
    
    # VPC
    resource "aws_vpc" "example_vpc" {
      cidr_block = "10.0.0.0/16"
      # Additional settings can be added here.
    }
    
    # Subnet
    resource "aws_subnet" "example_subnet" {
      vpc_id            = aws_vpc.example_vpc.id
      cidr_block        = "10.0.1.0/24"
      availability_zone = "us-west-2a"
    }
    
    # Security Group for EC2
    resource "aws_security_group" "example_sg" {
      name        = "example-sg"
      description = "Allow inbound SSH traffic"
      vpc_id      = aws_vpc.example_vpc.id
    
      ingress {
        from_port   = 22
        to_port     = 22
        protocol    = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
      }
    }
    
    # EC2 Instance
    resource "aws_instance" "example_instance" {
      ami                   = "ami-0c94855ba95c71c99"  # Use a dummy or test AMI ID for local testing
      instance_type         = "t2.micro"
      subnet_id             = aws_subnet.example_subnet.id
      vpc_security_group_ids = [aws_security_group.example_sg.id]
      key_name              = aws_key_pair.example_key.key_name
    }
    
    # EC2 Key Pair
    resource "aws_key_pair" "example_key" {
      key_name   = "example-key"
      public_key = file("~/.ssh/id_rsa.pub")
    }
    
    # S3 Bucket
    resource "aws_s3_bucket" "example_bucket" {
      bucket = "example-bucket"
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
    
    # S3 Bucket Policy
    resource "aws_s3_bucket_policy" "example_bucket_policy" {
      bucket = aws_s3_bucket.example_bucket.id
    
      policy = jsonencode({
        Version   = "2012-10-17",
        Statement = [
          {
            Sid       = "AllowPublicRead",
            Effect    = "Allow",
            Principal = "*",
            Action    = "s3:GetObject",
            Resource  = "${aws_s3_bucket.example_bucket.arn}/*"
          }
        ]
      })
    }
    
    # IAM Role for EC2 Instances
    resource "aws_iam_role" "example_ec2_role" {
      name        = "example-iam-role"
      description = "Role for EC2 instances"
      
      assume_role_policy = jsonencode({
        Version   = "2012-10-17",
        Statement = [{
          Action    = "sts:AssumeRole",
          Effect    = "Allow",
          Principal = { Service = "ec2.amazonaws.com" }
        }]
      })
    }
    
    # IAM Policy for EC2 Instances (S3 Access)
    resource "aws_iam_policy" "example_ec2_policy" {
      name        = "example-iam-policy"
      description = "Policy for EC2 instances to access S3"
      policy      = jsonencode({
        Version   = "2012-10-17",
        Statement = [{
          Action   = "s3:PutObject",
          Effect   = "Allow",
          Resource = "${aws_s3_bucket.example_bucket.arn}/*"
        }]
      })
    }
    
    # Attach IAM Policy to the Role
    resource "aws_iam_role_policy_attachment" "example_ec2_attachment" {
      role       = aws_iam_role.example_ec2_role.name
      policy_arn = aws_iam_policy.example_ec2_policy.arn
    }
        """
        prompt = f"""
        Given the following optimized AWS services:
        {optimized_services}
        And the following Terraform documentation:
        {terraform_docs}
        Generate a Terraform script that provisions these AWS resources in a cost-effective manner. 
        Follow the provided template only {template}. DO NOT provide any additional text along with the template, and do not add anything which is not there in the template.
        
        """
        return self.query_openrouter(prompt, TEMPLATE_MODEL)

    def start(self):
        # self.deploy_terraform()
        # uncommented above line if needed
        print("🔍 Reading AWS services required...")
        aws_services = self.read_aws_services()
        print("✅ AWS Services Extracted:", aws_services)

        print("📡 Querying Pinecone for Terraform modules...")
        terraform_docs = self.query_pinecone(aws_services.split())
        print("✅ Relevant Terraform Documentation Retrieved.")

        print("💰 Optimizing AWS service selection...")
        optimized_services = self.optimize_aws_services(
            aws_services, "\n\n".join(terraform_docs)
        )
        print("✅ Optimized AWS Services:", optimized_services)

        print("🛠️ Generating Terraform code...")
        terraform_script = self.generate_terraform_code(
            optimized_services, "\n\n".join(terraform_docs)
        )

        print("✅ Terraform Script Generated:")
        print(terraform_script)
        regex = rf"^(```terraform)+|(```)+$"
        # Use re.sub() to replace the matches with an empty string
        tf_script = re.sub(regex, "", terraform_script)

        with open("generated_terraform.tf", "w", encoding="utf-8") as f:
            f.write(tf_script)
        print("🎉 Terraform script saved as generated_terraform.tf")
        print("Creating Infrastructure on AWS....")
        # self.deploy_terraform(tf_script)
        print("✅ Infrastructure created.")


# def main():
#     # deploy_terraform()
#     print("🔍 Reading AWS services required...")
#     aws_services = read_aws_services()
#     print("✅ AWS Services Extracted:", aws_services)
#
#     print("📡 Querying Pinecone for Terraform modules...")
#     terraform_docs = query_pinecone(aws_services.split())
#     print("✅ Relevant Terraform Documentation Retrieved.")
#
#     print("💰 Optimizing AWS service selection...")
#     optimized_services = optimize_aws_services(
#         aws_services, "\n\n".join(terraform_docs)
#     )
#     print("✅ Optimized AWS Services:", optimized_services)
#
#     print("🛠️ Generating Terraform code...")
#     terraform_script = generate_terraform_code(
#         optimized_services, "\n\n".join(terraform_docs)
#     )
#
#     print("✅ Terraform Script Generated:")
#     print(terraform_script)
#     regex = rf'^(```terraform)+|(```)+$'
#     # Use re.sub() to replace the matches with an empty string
#     tf_script = re.sub(regex, '', terraform_script)
#
#     with open("generated_terraform.tf", "w", encoding="utf-8") as f:
#         f.write(tf_script)
#     print("🎉 Terraform script saved as generated_terraform.tf")
#     print("Creating Infrastructure on AWS....")
#     deploy_terraform(tf_script)
#     print("✅ Infrastructure created.")
#
#
# if __name__ == "__main__":
#     main()


# import os
# import boto3
# from dotenv import load_dotenv
# import openrouter


# class TerraformTemplateGenerator:
#     """
#     Class to interact with an LLM through OpenRouter, request files, and generate a Terraform template.

#     Attributes:
#         summaries (list): List of summaries of code files.
#         openrouter_api_key (str): API key for accessing OpenRouter's API.
#         terraform_template (str): The generated Terraform template.
#     """

#     def __init__(self, summaries, openrouter_api_key, aws_access_key_id, aws_secret_access_key,
#                  region_name="us-west-2"):
#         """
#         Initializes the TerraformTemplateGenerator with the necessary information.

#         Args:
#             summaries (list): A list of code file summaries.
#             openrouter_api_key (str): API key to access OpenRouter.
#             aws_access_key_id (str): AWS access key for authentication.
#             aws_secret_access_key (str): AWS secret key for authentication.
#             region_name (str): AWS region to deploy resources (default is us-west-2).
#         """
#         self.summaries = summaries
#         self.openrouter_api_key = openrouter_api_key
#         self.aws_access_key_id = aws_access_key_id
#         self.aws_secret_access_key = aws_secret_access_key
#         self.region_name = region_name
#         self.terraform_template = None

#         # Initialize AWS S3 client for optional push to AWS
#         self.s3_client = boto3.client(
#             's3',
#             aws_access_key_id=self.aws_access_key_id,
#             aws_secret_access_key=self.aws_secret_access_key,
#             region_name=self.region_name
#         )

#         # Initialize OpenRouter API key
#         openrouter.api_key = self.openrouter_api_key

#     def determine_required_files(self):
#         """
#         Make an API call to the LLM via OpenRouter to determine which files are required for the Terraform template.
#         """
#         prompt = f"""
#         You are an AI assistant that helps generate Terraform templates. You have been given the following summaries of code files:
#         {self.summaries}

#         Based on these summaries, identify which files are required to create a Terraform template.
#         Provide the names of the files required to generate the Terraform template.
#         """

#         response = openrouter.Completion.create(
#             model="google/gemini-exp-1206:free",  # Specify the model you want to use from OpenRouter
#             prompt=prompt,
#             max_tokens=150
#         )

#         required_files = response.choices[0].text.strip().split("\n")
#         return required_files

#     def request_files_from_system(self, required_files):
#         """
#         Request the local system for these files.
#         """
#         files = {}
#         for file in required_files:
#             try:
#                 with open(file, "r") as f:
#                     files[file] = f.read()
#             except FileNotFoundError:
#                 print(f"File {file} not found in the local system.")
#         return files

#     def generate_terraform_template(self, files):
#         """
#         Generate a Terraform template based on the required files' contents.
#         For simplicity, we will just concatenate the contents of the files and format them as a Terraform template.
#         """
#         template = "terraform {\n  required_providers {\n    aws = {\n      source = \"hashicorp/aws\"\n      version = \"~> 3.0\"\n    }\n  }\n}\n"

#         # Simple placeholder logic for generating a terraform template
#         for filename, content in files.items():
#             template += f"\n# Contents from {filename}\n"
#             template += content + "\n"

#         self.terraform_template = template
#         return self.terraform_template

#     def push_to_aws(self, bucket_name, terraform_file_name="terraform_template.tf"):
#         """
#         Push the generated Terraform template to AWS S3.
#         """
#         if self.terraform_template:
#             try:
#                 # Upload the Terraform template to an S3 bucket
#                 self.s3_client.put_object(
#                     Bucket=bucket_name,
#                     Key=terraform_file_name,
#                     Body=self.terraform_template
#                 )
#                 print(f"Terraform template uploaded to S3 bucket {bucket_name} as {terraform_file_name}")
#             except Exception as e:
#                 print(f"Error uploading to AWS: {e}")
#         else:
#             print("No Terraform template to upload.")

#     def execute(self, bucket_name):
#         """
#         The main function that coordinates the steps to generate and optionally upload the Terraform template.
#         """
#         required_files = self.determine_required_files()
#         print(f"Required files: {required_files}")

#         # Request the files from the local system
#         files = self.request_files_from_system(required_files)

#         if files:
#             terraform_template = self.generate_terraform_template(files)
#             print("Terraform Template Generated:\n", terraform_template)

#             # Optionally push to AWS
#             self.push_to_aws(bucket_name)
#         else:
#             print("No files found to generate the Terraform template.")


# Usage Example:
# if __name__ == "__main__":
#     load_dotenv()  # Load environment variables from .env file
#
#     # Assuming .env has the necessary keys
#     summaries = [
#         "This file contains AWS EC2 instance configuration.",
#         "This file defines the security groups for the EC2 instances.",
#         "This file is for setting up an S3 bucket and related resources."
#     ]
#
#     # Assuming you have set up these environment variables in your .env file
#     openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
#     aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
#     aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
#
#     generator = TerraformTemplateGenerator(
#         summaries,
#         openrouter_api_key,
#         aws_access_key_id,
#         aws_secret_access_key
#     )
#
#     # Specify your S3 bucket name
#     generator.execute(bucket_name="your-terraform-bucket")
