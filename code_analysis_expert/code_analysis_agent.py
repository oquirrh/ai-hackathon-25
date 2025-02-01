import os
import ollama
from langchain.text_splitter import CharacterTextSplitter
from dotenv import load_dotenv

load_dotenv()

# Define the model name for Ollama
model_name = "llama3.2:1b"  # Modify this if needed, as per your local setup


class CodeAnalysisAgent:
    def __init__(self, model_name):
        """
        Initializes the agent with the local Ollama model.

        Args:
            model_name (str): Ollama model identifier (e.g., llama3.2 1b)
        """
        # Setup text splitter
        self.text_splitter = CharacterTextSplitter(chunk_size=1500, chunk_overlap=100)
        self.model_name = model_name

    def summarize_code(self, file_path, all_files_content):
        """
        Summarizes the content of a code file and highlights interactions with other files.
        If the file is too large, it chunks the file into smaller parts and summarizes them iteratively.

        Args:
            file_path (str): The path of the code file to be summarized.
            all_files_content (dict): Dictionary containing the content of all files in the codebase.
        """

        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        # Split content into chunks
        chunks = self.text_splitter.split_text(content)

        # Summarize each chunk using Ollama's API
        chunk_summaries = []
        for chunk in chunks:
            prompt = f"Please summarize the following code from the file '{file_path}'. Provide only the file path (from root) and summary, and no suggestions for improvement. \n{chunk}"
            response = ollama.chat(model=self.model_name, messages=[{"role": "user", "content": prompt}])
            chunk_summaries.append(response.message.content)

        # Summarize the interactions with other files by providing context of all files
        # interaction_summary = self.summarize_interactions(file_path, all_files_content)

        # Combine chunk summaries and interactions
        overall_summary = " ".join(chunk_summaries)
        return overall_summary

    def summarize_interactions(self, file_path, all_files_content):
        """
        Asks the model to summarize how the given file interacts with other files in the codebase.

        Args:
            file_path (str): The path of the code file being summarized.
            all_files_content (dict): Dictionary containing the content of all files in the codebase.
        """
        related_files = [file for file in all_files_content if file != file_path]
        interaction_prompt = f"""
        You are an AI assistant analyzing a codebase. The file at {file_path} is part of this codebase.
        Your task is to summarize how the file interacts with other files in the codebase.
        Below are the contents of all the files in the codebase, including the file in question:

        {file_path}:
        {all_files_content[file_path]}

        Interactions with other files:
        """

        # Send prompt to Ollama for interaction summary
        response = ollama.chat(model=self.model_name, messages=[{"role": "user", "content": interaction_prompt}])
        interaction_summary = response["text"]
        return interaction_summary

    def analyze_directory(self, dir_path):
        """
        Analyzes all code files in a directory (and subdirectories), summarizes their purpose,
        and returns a dictionary with file paths as keys and their summaries as values.

        Args:
            dir_path (str): The path of the directory to analyze.
        """
        summaries = {}
        all_files_content = {}

        # Collect all code files (could be Python, Java, C++, etc.)
        for root, _, files in os.walk(dir_path):
            for file in files:
                if file.endswith(
                        (".py", ".js", ".java", ".cpp", ".c", ".rb", ".go", ".php", ".ts")):  # Add more file types
                    file_path = os.path.join(root, file)
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        all_files_content[file_path] = f.read()

        file_path_dict = {}
        counter = 0
        for item in file_path:
            file_path_dict[file_path] = counter
            counter = counter + 1
        # Analyze each file and check for interactions with other files
        for file_path, content in all_files_content.items():
            print(f"Summarizing {file_path}...")
            summary= self.summarize_code(file_path, all_files_content)
            summaries[file_path] = summary

        return summaries, file_path_dict


if __name__ == '__main__':
    agent = CodeAnalysisAgent(model_name=model_name)
    summaries = agent.analyze_directory("/Users/aaditya/Learning/hackathon/nestJs_demo")
    for file_path, summary in summaries.items():
        print(f"Summary for {file_path}:\n{summary}\n")
