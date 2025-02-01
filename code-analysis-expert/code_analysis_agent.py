import os
from langchain.text_splitter import CharacterTextSplitter
from transformers import AutoTokenizer, AutoModelForCausalLM
from dotenv import load_dotenv

load_dotenv()
# Define the model path (Hugging Face model identifier)
model_name = "codellama/CodeLlama-3b-hf"  # Change to a code-focused model


class CodeAnalysisAgent:
    def __init__(self, model_name):
        """
        Initializes the agent with the Hugging Face model.

        Args:
            model_name (str): Hugging Face model identifier (e.g., CodeBERT, CodeT5, etc.)
        """
        # Load the tokenizer and model from Hugging Face
        # Load model directly
        self.tokenizer = AutoTokenizer.from_pretrained("deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B")
        self.model = AutoModelForCausalLM.from_pretrained("deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B")

        # Setup text splitter
        self.text_splitter = CharacterTextSplitter(chunk_size=1500, chunk_overlap=100)

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

        # Summarize each chunk
        chunk_summaries = []
        for chunk in chunks:
            inputs = self.tokenizer.encode(chunk, return_tensors="pt", max_length=1024, truncation=True)
            outputs = self.model.generate(inputs, max_new_tokens=256, num_beams=5, early_stopping=True)
            summary = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            chunk_summaries.append(summary)

        # Summarize the interactions with other files by providing context of all files
        interaction_summary = self.summarize_interactions(file_path, all_files_content)

        # Combine chunk summaries and interactions
        overall_summary = " ".join(chunk_summaries) + " " + interaction_summary
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

        # Provide the model with content from all files for context
        inputs = self.tokenizer.encode(interaction_prompt, return_tensors="pt", max_length=2048, truncation=True)
        outputs = self.model.generate(inputs, max_length=512, num_beams=5, early_stopping=True)
        interaction_summary = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return interaction_summary

    from tqdm import tqdm

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

        # Add progress tracking for summarizing each file
        for file_path in tqdm(all_files_content.keys(), desc="Summarizing files", unit="file"):
            content = all_files_content[file_path]
            print(f"Summarizing {file_path}...")
            summary = self.summarize_code(file_path, all_files_content)
            summaries[file_path] = summary

        return summaries


if __name__ == '__main__':
    agent = CodeAnalysisAgent(model_name=model_name)
    summaries = agent.analyze_directory("/Users/aaditya/Learning/hackathon/ai-hackathon-25/llama.cpp/src/")
    for file_path, summary in summaries.items():
        print(f"Summary for {file_path}:\n{summary}\n")
