# import stuff

class AIPipeline:
    def __init__(self, agents):
        """
        Initialize the pipeline with a list of agents.
        :param agents: List of agent instances to execute sequentially.
        """
        self.agents = agents

    def start_pipeline(self, model_path, code_directory_path):
        pass

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
