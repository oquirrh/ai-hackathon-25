import dspy
from dspy.teleprompt import BootstrapFewShot
from typing import List, Dict
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# Configure DSPy with OpenRouter
class OpenRouterConfig(dspy.Config):
    def __init__(self):
        super().__init__()
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.model = "meta-llama/llama-3-8b-instruct:free"


# Define structured predictor modules
class ServiceIdentifier(dspy.Signature):
    """Identifies required AWS services from project content."""

    context = dspy.InputField(desc="Project files content")
    services = dspy.OutputField(
        desc="List of required AWS services with justifications"
    )


class TerraformGenerator(dspy.Signature):
    """Generates Terraform configuration based on identified services."""

    services = dspy.InputField(desc="List of required AWS services")
    terraform_config = dspy.OutputField(desc="Complete Terraform configuration")


class FileAnalyzer(dspy.Signature):
    """Analyzes project structure to identify relevant files."""

    project_structure = dspy.InputField(desc="Complete project file structure")
    relevant_files = dspy.OutputField(
        desc="List of files needed for AWS service analysis"
    )


class TerraformExpert:
    def __init__(self):
        # Initialize DSPy with OpenRouter
        dspy.settings.configure(model=OpenRouterConfig())

        # Initialize predictors
        self.file_analyzer = dspy.Predict(FileAnalyzer)
        self.service_identifier = dspy.Predict(ServiceIdentifier)
        self.terraform_generator = dspy.Predict(TerraformGenerator)

        # Bootstrap with examples if available
        self._bootstrap_models()

    def _bootstrap_models(self):
        """Bootstrap models with few-shot examples."""
        examples = [
            # File analysis examples
            (
                ("requirements.txt\nDockerfile\nsrc/app.py\n",),
                ["requirements.txt", "Dockerfile", "src/app.py"],
            ),
            # Service identification examples
            (
                ("Flask web app with S3 storage\n",),
                ["AWS EC2 (t2.micro) for web server", "AWS S3 for file storage"],
            ),
            # Terraform generation examples
            (
                ("AWS EC2 t2.micro, AWS S3",),
                """resource "aws_instance" "web" {
                ami           = "ami-0c55b159cbfafe1f0"
                instance_type = "t2.micro"
             }""",
            ),
        ]

        bootstrapper = BootstrapFewShot(train_data=examples)
        bootstrapper.bootstrap(
            [self.file_analyzer, self.service_identifier, self.terraform_generator]
        )

    def analyze_project(self, project_structure: str) -> Dict:
        """Analyzes project and generates Terraform configuration."""

        # Step 1: Identify relevant files
        relevant_files = self.file_analyzer(project_structure=project_structure)

        # Step 2: Read file contents
        file_contents = self._read_files(relevant_files.relevant_files)

        # Step 3: Identify required services
        services = self.service_identifier(context=file_contents)

        # Step 4: Generate Terraform configuration
        terraform_config = self.terraform_generator(services=services.services)

        return {
            "relevant_files": relevant_files.relevant_files,
            "required_services": services.services,
            "terraform_config": terraform_config.terraform_config,
        }

    def _read_files(self, file_paths: List[str]) -> str:
        """Reads contents of specified files."""
        contents = []
        for path in file_paths:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    contents.append(f"--- {path} ---\n{f.read()}")
            except Exception as e:
                print(f"Warning: Could not read {path}: {e}")
        return "\n\n".join(contents)

    def save_terraform_config(
        self, config: str, output_path: str = "generated_terraform.tf"
    ):
        """Saves generated Terraform configuration to file."""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(config)
        print(f"✅ Terraform configuration saved to {output_path}")


def main():
    # Example usage
    project_path = "."  # Current directory

    # Initialize expert system
    expert = TerraformExpert()

    # Get project structure
    project_structure = os.popen(f"find {project_path} -type f").read()

    # Analyze project and generate Terraform config
    result = expert.analyze_project(project_structure)

    # Save the generated configuration
    expert.save_terraform_config(result["terraform_config"])

    print("✨ Analysis complete!")
    print("\n📁 Relevant files:", result["relevant_files"])
    print("\n🚀 Required AWS services:", result["required_services"])


if __name__ == "__main__":
    main()
