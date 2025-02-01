# import stuff
from code_analysis_expert.code_analysis_agent import CodeAnalysisAgent
from terraform_template_expert.terraform_gen_agent import TerraformTemplateGenerator
import os

class AIPipeline:
    def __init__(self, agents):
        """
        Initialize the pipeline with a list of agents.
        :param agents: List of agent instances to execute sequentially.
        """
        self.model_name="llama3.2:1b"
        self.agents = agents

    def start_pipeline(self):
        agent = CodeAnalysisAgent(model_name=self.model_name)
        summaries = agent.analyze_directory("/Users/aaditya/Learning/hackathon/nestJs_demo")
        openrouter_api_key = "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"
        aws_access_key_id = "aws"
        aws_secret_access_key = "aws"
        generator = TerraformTemplateGenerator(
            summaries,
            openrouter_api_key,
            aws_access_key_id,
            aws_secret_access_key
        )
        generator.execute(bucket_name="your-terraform-bucket")

    def execute(self, input_data):
        """
        Execute the pipeline by passing data through each agent sequentially.
        :param input_data: The initial input to the pipeline.
        :return: The final output after processing by all agents.
        """
        # todo needs modification
        current_data = input_data
        for agent in self.agents:
            print(f"Passing data to {agent.__class__.__name__}...")
            current_data = agent.process(current_data)
            print(f"Output from {agent.__class__.__name__}: {current_data}\n")

        return current_data

if __name__ == '__main__':
    pipe = AIPipeline([])
    pipe.start_pipeline()
