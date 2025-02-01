import dspy
from dspy.teleprompt import BootstrapFewShot
from typing import List, Dict, Optional, Tuple
import os
import json
import hashlib
from pathlib import Path
import boto3
from dotenv import load_dotenv
import hcl2  # For parsing existing Terraform
import yaml

# Load environment variables
load_dotenv()

class InfrastructureMetrics:
    """Tracks and validates infrastructure decisions"""
    def __init__(self):
        self.cost_estimates = {}
        self.performance_metrics = {}
        self.security_scores = {}
        
    def estimate_costs(self, services: List[str]) -> Dict:
        """Estimates monthly costs for proposed services"""
        # Implementation would use AWS Price List API
        pass

    def evaluate_security(self, config: str) -> Dict:
        """Evaluates security posture of proposed infrastructure"""
        # Implementation would use AWS Config rules
        pass

class ResourceOptimizer:
    """Optimizes AWS resource selections"""
    def __init__(self):
        self.historical_data = {}
        self.performance_targets = {}
        
    def suggest_optimizations(self, current_config: str) -> List[str]:
        """Suggests improvements to current configuration"""
        pass

class TerraformValidator:
    """Validates and tests Terraform configurations"""
    @staticmethod
    def validate_syntax(config: str) -> Tuple[bool, str]:
        """Validates Terraform syntax"""
        try:
            parsed = hcl2.loads(config)
            return True, "Valid Terraform configuration"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def check_best_practices(config: str) -> List[str]:
        """Checks adherence to Terraform best practices"""
        issues = []
        # Add checks for tags, state management, etc.
        return issues

class FileAnalyzer(dspy.Signature):
    """Enhanced file analysis with better context understanding"""
    project_structure = dspy.InputField(desc="Project file structure")
    existing_config = dspy.InputField(desc="Existing Terraform configuration if any")
    analysis_result = dspy.OutputField(desc="Detailed analysis of project requirements")

class ServiceRecommender(dspy.Signature):
    """Recommends optimal AWS services based on requirements"""
    analysis = dspy.InputField(desc="Project analysis")
    constraints = dspy.InputField(desc="Performance and cost constraints")
    recommendations = dspy.OutputField(desc="Optimized service recommendations")

class TerraformGenerator(dspy.Signature):
    """Generates or updates Terraform configurations"""
    recommendations = dspy.InputField(desc="Service recommendations")
    existing_config = dspy.InputField(desc="Existing Terraform configuration")
    constraints = dspy.InputField(desc="Infrastructure constraints")
    terraform_config = dspy.OutputField(desc="Generated Terraform configuration")

class TerraformExpert:
    def __init__(self, config_path: Optional[str] = None):
        # Initialize DSPy with configuration
        dspy.settings.configure(model=self._setup_model_config())
        
        # Initialize components
        self.metrics = InfrastructureMetrics()
        self.optimizer = ResourceOptimizer()
        self.validator = TerraformValidator()
        
        # Initialize DSPy predictors
        self.file_analyzer = dspy.Predict(FileAnalyzer)
        self.service_recommender = dspy.Predict(ServiceRecommender)
        self.terraform_generator = dspy.Predict(TerraformGenerator)
        
        # Load configuration if provided
        self.config = self._load_config(config_path)
        
        # Setup state management
        self.state_manager = self._initialize_state_manager()
        
        # Bootstrap with examples
        self._bootstrap_models()

    def _setup_model_config(self):
        """Sets up the LLM configuration"""
        return {
            "model": os.getenv("LLM_MODEL", "meta-llama/llama-3-8b-instruct:free"),
            "api_key": os.getenv("OPENROUTER_API_KEY"),
            "temperature": 0.3  # Lower temperature for more consistent outputs
        }

    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Loads configuration with defaults"""
        default_config = {
            "cost_constraints": {"monthly_max": 1000},
            "performance_targets": {"latency_ms": 100},
            "security_requirements": {"compliance_level": "high"},
        }
        
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return {**default_config, **yaml.safe_load(f)}
        return default_config

    def _initialize_state_manager(self):
        """Initializes Terraform state management"""
        return boto3.client('s3') if os.getenv('AWS_ACCESS_KEY_ID') else None

    def _bootstrap_models(self):
        """Enhanced bootstrapping with comprehensive examples"""
        examples = self._load_training_examples()
        bootstrapper = BootstrapFewShot(train_data=examples)
        bootstrapper.bootstrap([
            self.file_analyzer,
            self.service_recommender,
            self.terraform_generator
        ])

    def _load_training_examples(self) -> List:
        """Loads training examples from file or embedded defaults"""
        example_path = "training_examples.json"
        if os.path.exists(example_path):
            with open(example_path, 'r') as f:
                return json.load(f)
        return self._get_default_examples()

    def _get_default_examples(self) -> List:
        """Provides default training examples"""
        return [
            # Comprehensive examples for different project types
            {
                "input": {
                    "project_structure": "web_app/\n  app.py\n  requirements.txt\n  Dockerfile",
                    "existing_config": "",
                    "constraints": {"monthly_max": 500}
                },
                "output": {
                    "services": [
                        "AWS ECS Fargate (serverless containers)",
                        "AWS Application Load Balancer",
                        "AWS RDS Aurora Serverless"
                    ],
                    "terraform_config": """
                    module "ecs" {
                        source = "terraform-aws-modules/ecs/aws"
                        # Configuration details...
                    }
                    """
                }
            },
            # Add more examples...
        ]

    async def analyze_project(self, 
                            project_path: str, 
                            existing_terraform: Optional[str] = None,
                            constraints: Optional[Dict] = None) -> Dict:
        """Analyzes project and generates/updates Terraform configuration"""
        
        # Get project structure
        project_structure = self._scan_project(project_path)
        
        # Load existing Terraform if any
        existing_config = self._load_existing_terraform(existing_terraform)
        
        # Analyze project requirements
        analysis = await self.file_analyzer(
            project_structure=project_structure,
            existing_config=existing_config
        )
        
        # Get service recommendations
        recommendations = await self.service_recommender(
            analysis=analysis.analysis_result,
            constraints=constraints or self.config
        )
        
        # Generate or update Terraform
        terraform_result = await self.terraform_generator(
            recommendations=recommendations.recommendations,
            existing_config=existing_config,
            constraints=constraints or self.config
        )
        
        # Validate and optimize
        validated_config = self._validate_and_optimize(terraform_result.terraform_config)
        
        return {
            "analysis": analysis.analysis_result,
            "recommendations": recommendations.recommendations,
            "terraform_config": validated_config,
            "metrics": self._generate_metrics(validated_config)
        }

    def _scan_project(self, project_path: str) -> str:
        """Enhanced project scanning with intelligent file filtering"""
        ignore_patterns = self._load_ignore_patterns(project_path)
        
        files = []
        for path in Path(project_path).rglob('*'):
            if self._should_include_file(path, ignore_patterns):
                files.append(str(path.relative_to(project_path)))
        
        return '\n'.join(sorted(files))

    def _load_ignore_patterns(self, project_path: str) -> List[str]:
        """Loads patterns of files to ignore"""
        patterns = {'.git', 'node_modules', '__pycache__', '*.pyc'}
        
        gitignore_path = Path(project_path) / '.gitignore'
        if gitignore_path.exists():
            patterns.update(gitignore_path.read_text().splitlines())
            
        return patterns

    def _should_include_file(self, path: Path, ignore_patterns: List[str]) -> bool:
        """Determines if a file should be included in analysis"""
        return not any(path.match(pattern) for pattern in ignore_patterns)

    def _load_existing_terraform(self, path: Optional[str]) -> str:
        """Loads and parses existing Terraform configuration"""
        if not path:
            return ""
            
        try:
            with open(path, 'r') as f:
                return f.read()
        except Exception as e:
            print(f"Warning: Could not load existing Terraform: {e}")
            return ""

    def _validate_and_optimize(self, config: str) -> str:
        """Validates and optimizes Terraform configuration"""
        # Validate syntax
        is_valid, message = self.validator.validate_syntax(config)
        if not is_valid:
            raise ValueError(f"Invalid Terraform configuration: {message}")
            
        # Check best practices
        issues = self.validator.check_best_practices(config)
        if issues:
            print("Warning: Best practice issues found:", issues)
            
        # Optimize resources
        optimizations = self.optimizer.suggest_optimizations(config)
        if optimizations:
            print("Suggested optimizations:", optimizations)
            
        return config

    def _generate_metrics(self, config: str) -> Dict:
        """Generates metrics for the infrastructure"""
        return {
            "estimated_costs": self.metrics.estimate_costs(config),
            "security_score": self.metrics.evaluate_security(config),
            "optimization_score": len(self.optimizer.suggest_optimizations(config))
        }

    def save_config(self, 
                   config: str, 
                   path: str = "generated_terraform",
                   version: Optional[str] = None) -> str:
        """Saves Terraform configuration with versioning"""
        # Create directory if it doesn't exist
        os.makedirs(path, exist_ok=True)
        
        # Generate version if not provided
        if not version:
            version = hashlib.md5(config.encode()).hexdigest()[:8]
            
        # Save configuration
        file_path = f"{path}/main_{version}.tf"
        with open(file_path, 'w') as f:
            f.write(config)
            
        # Save metadata
        metadata = {
            "version": version,
            "timestamp": str(datetime.now()),
            "metrics": self._generate_metrics(config)
        }
        
        with open(f"{path}/metadata_{version}.json", 'w') as f:
            json.dump(metadata, f, indent=2)
            
        return file_path

async def main():
    # Initialize expert system with custom configuration
    expert = TerraformExpert(config_path="terraform_config.yaml")
    
    # Analyze project and generate/update Terraform
    result = await expert.analyze_project(
        project_path=".",
        existing_terraform="existing_terraform.tf" if os.path.exists("existing_terraform.tf") else None,
        constraints={
            "monthly_max": 1000,
            "performance_targets": {"latency_ms": 100}
        }
    )
    
    # Save the results
    config_path = expert.save_config(result["terraform_config"])
    
    print(f"✨ Analysis complete! Configuration saved to: {config_path}")
    print("\n📊 Infrastructure Metrics:")
    print(json.dumps(result["metrics"], indent=2))

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())