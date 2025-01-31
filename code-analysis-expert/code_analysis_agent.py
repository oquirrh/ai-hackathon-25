import os
from langchain.text_splitter import CharacterTextSplitter
from llama_cpp import Llama
from dotenv import load_dotenv

load_dotenv()
local_model_path = os.getenv("LOCAL_MODEL_PATH")


class CodeAnalysisAgent:

    def __init__(self, model_path):
        self.model_path = model_path
        if not os.path.exists(local_model_path):
            print(f"Model not found at: {local_model_path}")
        self.llm = Llama(self.model_path, n_ctx=2048)
        self.text_splitter = CharacterTextSplitter(chunk_size=1500, chunk_overlap=100)

    def summarize_code(self, file_path):
        """
        Summarizes the content of a code file. If the file is too large, it chunks the file
        into smaller parts and summarizes them iteratively.
        """
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        # Split content into chunks
        chunks = self.text_splitter.split_text(content)

        # Summarize each chunk
        chunk_summaries = []
        for chunk in chunks:
            prompt = f"""
            You are an AI assistant analyzing code files. Summarize the purpose of the following code:

            {chunk}

            Summary:
            """
            response = self.llm(prompt, max_tokens=256)
            chunk_summaries.append(response["choices"][0]["text"].strip())

        # Combine chunk summaries and summarize the overall file
        overall_prompt = f"""
        You are an AI assistant analyzing the following summaries of a code file. Summarize the overall purpose of the code based on these summaries:

        {''.join(chunk_summaries)}

        Overall Summary:
        """
        overall_response = self.llm(overall_prompt, max_tokens=256)
        return overall_response["choices"][0]["text"].strip()

    def analyze_directory(self, dir_path):
        """
        Analyzes all code files in a directory (and subdirectories), summarizes their purpose,
        and returns a dictionary with file paths as keys and their summaries as values.
        """
        summaries = {}
        for root, _, files in os.walk(dir_path):
            for file in files:
                if file.endswith(".py"):  # You can filter for other file types as needed
                    file_path = os.path.join(root, file)
                    print(f"Summarizing {file_path}...")
                    summary = self.summarize_code(file_path)
                    summaries[file_path] = summary
        return summaries


if __name__ == '__main__':
    agent = CodeAnalysisAgent(model_path=local_model_path)
    summaries = agent.analyze_directory("/path/to/code/directory")
    for file_path, summary in summaries.items():
        print(f"Summary for {file_path}:\n{summary}\n")
# Usage example
# agent = CodeAnalysisAgent(model_path=local_model_path)
# summaries = agent.analyze_directory("/path/to/code/directory")
# for file_path, summary in summaries.items():
#     print(f"Summary for {file_path}:\n{summary}\n")


