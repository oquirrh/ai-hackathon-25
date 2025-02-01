import os
import ollama
from pathspec import PathSpec
from pathspec.patterns.gitwildmatch import GitWildMatchPattern
from langchain.text_splitter import CharacterTextSplitter
from dotenv import load_dotenv

load_dotenv()

model_name = "qwen2.5-coder"

class CodeAnalysisAgent:
    def __init__(self, model_name):
        self.text_splitter = CharacterTextSplitter(chunk_size=1500, chunk_overlap=100)
        self.model_name = model_name
        self.terraform_exts = (".tf", ".tfvars", ".hcl")

    def summarize_code(self, file_path, all_files_content):
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception as e:
            return f"Error reading file: {str(e)}"

        chunks = self.text_splitter.split_text(content)
        chunk_summaries = []

        for chunk in chunks:
            prompt = f"""Analyze this Terraform configuration from '{file_path}' and identify:
1. Cloud providers/services used
2. Resource definitions and dependencies
3. Variables/Outputs/Data sources
4. Network and security configurations
5. State management setup
Provide concise technical summary:\n{chunk}"""

            try:
                response = ollama.chat(model=self.model_name, messages=[{"role": "user", "content": prompt}])
                chunk_summaries.append(response.message.content)
            except Exception as e:
                chunk_summaries.append(f"API Error: {str(e)}")

        return "\n".join(chunk_summaries)

    def analyze_directory(self, dir_path):
            summaries = {}
            print(f"Starting analysis of directory: {dir_path}")

            for root, dirs, files in os.walk(dir_path, topdown=True):
                gitignore_path = os.path.join(root, '.gitignore')
                spec = PathSpec([])
                if os.path.exists(gitignore_path):
                    with open(gitignore_path, 'r') as f:
                        spec = PathSpec.from_lines(GitWildMatchPattern, f)

                # 1. Skip ignored directories
                dirs[:] = [
                    d for d in dirs
                    if not spec.match_file(os.path.join(d))  # Check dir patterns
                ]

                # 2. Process all files, only skipping those ignored by .gitignore
                for file in files:
                    full_path = os.path.join(root, file)

                    # 3. Calculate proper relative path for .gitignore matching
                    rel_to_root = os.path.relpath(full_path, dir_path)
                    rel_to_current = os.path.relpath(full_path, root)

                    # Check against all relevant .gitignore specs
                    if spec.match_file(rel_to_current):
                        print(f"Ignoring {rel_to_root} (matches local .gitignore)")
                        continue

                    print(f"Processing: {rel_to_root}")
                    try:
                        summary = self.summarize_code(full_path, {})
                        summaries[full_path] = summary
                    except Exception as e:
                        print(f"Failed to analyze file {full_path}: {str(e)}")  # Corrected variable name here
                        summaries[full_path] = f"Analysis failed: {str(e)}"  # Corrected variable name here

            return summaries  # Added return statement


if __name__ == '__main__':
    agent = CodeAnalysisAgent(model_name=model_name)
    summaries = agent.analyze_directory("/path/to/terraform/config")
    for file_path, summary in summaries.items():
        print(f"Summary for {file_path}:\n{summary}\n")
