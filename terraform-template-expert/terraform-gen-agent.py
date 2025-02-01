import os
import boto3
from dotenv import load_dotenv
import openrouter


class TerraformTemplateGenerator:
    """
    Class to interact with an LLM through OpenRouter, request files, and generate a Terraform template.

    Attributes:
        summaries (list): List of summaries of code files.
        openrouter_api_key (str): API key for accessing OpenRouter's API.
        terraform_template (str): The generated Terraform template.
    """

    def __init__(self, summaries, openrouter_api_key, aws_access_key_id, aws_secret_access_key,
                 region_name="us-west-2"):
        """
        Initializes the TerraformTemplateGenerator with the necessary information.

        Args:
            summaries (list): A list of code file summaries.
            openrouter_api_key (str): API key to access OpenRouter.
            aws_access_key_id (str): AWS access key for authentication.
            aws_secret_access_key (str): AWS secret key for authentication.
            region_name (str): AWS region to deploy resources (default is us-west-2).
        """
        self.summaries = summaries
        self.openrouter_api_key = openrouter_api_key
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.region_name = region_name
        self.terraform_template = None

        # Initialize AWS S3 client for optional push to AWS
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.region_name
        )

        # Initialize OpenRouter API key
        openrouter.api_key = self.openrouter_api_key

    def determine_required_files(self):
        """
        Make an API call to the LLM via OpenRouter to determine which files are required for the Terraform template.
        """
        prompt = f"""
        You are an AI assistant that helps generate Terraform templates. You have been given the following summaries of code files:
        {self.summaries}

        Based on these summaries, identify which files are required to create a Terraform template.
        Provide the names of the files required to generate the Terraform template.
        """

        response = openrouter.Completion.create(
            model="google/gemini-exp-1206:free",  # Specify the model you want to use from OpenRouter
            prompt=prompt,
            max_tokens=150
        )

        required_files = response.choices[0].text.strip().split("\n")
        return required_files

    def request_files_from_system(self, required_files):
        """
        Request the local system for these files.
        """
        files = {}
        for file in required_files:
            try:
                with open(file, "r") as f:
                    files[file] = f.read()
            except FileNotFoundError:
                print(f"File {file} not found in the local system.")
        return files

    def generate_terraform_template(self, files):
        """
        Generate a Terraform template based on the required files' contents.
        For simplicity, we will just concatenate the contents of the files and format them as a Terraform template.
        """
        template = "terraform {\n  required_providers {\n    aws = {\n      source = \"hashicorp/aws\"\n      version = \"~> 3.0\"\n    }\n  }\n}\n"

        # Simple placeholder logic for generating a terraform template
        for filename, content in files.items():
            template += f"\n# Contents from {filename}\n"
            template += content + "\n"

        self.terraform_template = template
        return self.terraform_template

    def push_to_aws(self, bucket_name, terraform_file_name="terraform_template.tf"):
        """
        Push the generated Terraform template to AWS S3.
        """
        if self.terraform_template:
            try:
                # Upload the Terraform template to an S3 bucket
                self.s3_client.put_object(
                    Bucket=bucket_name,
                    Key=terraform_file_name,
                    Body=self.terraform_template
                )
                print(f"Terraform template uploaded to S3 bucket {bucket_name} as {terraform_file_name}")
            except Exception as e:
                print(f"Error uploading to AWS: {e}")
        else:
            print("No Terraform template to upload.")

    def execute(self, bucket_name):
        """
        The main function that coordinates the steps to generate and optionally upload the Terraform template.
        """
        required_files = self.determine_required_files()
        print(f"Required files: {required_files}")

        # Request the files from the local system
        files = self.request_files_from_system(required_files)

        if files:
            terraform_template = self.generate_terraform_template(files)
            print("Terraform Template Generated:\n", terraform_template)

            # Optionally push to AWS
            self.push_to_aws(bucket_name)
        else:
            print("No files found to generate the Terraform template.")


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
