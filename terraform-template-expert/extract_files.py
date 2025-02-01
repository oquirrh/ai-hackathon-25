import os
import sys
import subprocess
import requests
import json
import pathspec
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# OpenRouter API Key
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


class FileExtractor:
    # Function to query OpenRouter (or another LLM like Ollama)

    def __init__(self):
        return

    def query_llm(self, prompt):
        """
        Sends a prompt to OpenRouter API to get AI-generated responses.

        Args:
            prompt (str): The message to send to the LLM.

        Returns:
            str: The response from the LLM.
        """
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "microsoft/phi-3-mini-128k-instruct:free",  # Change model if needed
            "messages": [
                {
                    "role": "system",
                    "content": prompt,
                },
            ],
        }

        response = requests.post(url, json=payload, headers=headers)

        if response.status_code != 200:
            print(f"❌ API Error: {response.status_code} - {response.text}")
            sys.exit(1)

        json_response = response.json()

        # Extract the LLM-generated file list
        necessary_files_text = json_response["choices"][0]["message"]["content"]

        # Clean and standardize file paths
        necessary_files = list(
            set(  # Remove duplicates
                f.strip()
                for f in necessary_files_text.split("\n")
                if f.strip()  # Remove empty lines & extra spaces
            )
        )

        return necessary_files

    def load_gitignore_patterns(self, project_dir):
        """
        Reads the .gitignore file and returns a PathSpec object with ignore patterns.

        Args:
            project_dir (str): Path to the project directory.

        Returns:
            pathspec.PathSpec: PathSpec object containing ignore rules.
        """
        gitignore_path = os.path.join(project_dir, ".gitignore")

        ignore_patterns = [
            ".git/",  # Ensure .git folder is excluded
            ".gitignore",  # Exclude .gitignore itself
        ]

        if os.path.exists(gitignore_path):
            with open(gitignore_path, "r", encoding="utf-8") as gitignore_file:
                ignore_patterns.extend(gitignore_file.readlines())

        return pathspec.PathSpec.from_lines("gitwildmatch", ignore_patterns)

    def extract_project_structure(self, project_dir):
        """
        Extracts the file structure of the given project directory while respecting .gitignore.

        Args:
            project_dir (str): Path to the project directory.

        Returns:
            str: The filtered list of files in the project.
        """
        project_structure_file = "project_structure.txt"

        find_command = ["find", project_dir, "-type", "f"]

        exclude_dir = "ai-hackathon-25"  # Exclude cloned directory
        find_command += ["!", "-path", os.path.join(project_dir, exclude_dir, "*")]

        result = subprocess.run(find_command, capture_output=True, text=True)

        all_files = result.stdout.strip().split("\n")

        # Load .gitignore patterns
        ignore_spec = self.load_gitignore_patterns(project_dir)

        if ignore_spec:
            filtered_files = [
                f
                for f in all_files
                if not ignore_spec.match_file(os.path.relpath(f, project_dir))
            ]
        else:
            filtered_files = all_files  # No filtering if .gitignore is missing

        # Save the filtered file list
        # with open(project_structure_file, "w", encoding="utf-8") as file:
        #     file.write("\n".join(filtered_files))

        return "\n".join(filtered_files)

    def extract_file_contents(self, necessary_files):
        """
        Extracts the content of specified files from the project directory.

        Args:
            project_dir (str): Path to the project directory.
            necessary_files (list): List of filenames to extract content from.

        Returns:
            dict: A dictionary with file paths as keys and their content as values.
        """
        extracted_contents = {}

        for file_path in necessary_files:
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        extracted_contents[file_path] = f.read()
                except Exception as e:
                    print(f"⚠ WARNING: Could not read {file_path} - {e}")
            else:
                print(f"⚠️ WARNING: {file_path} not found in project directory.")

        return extracted_contents

    def save_extracted_content(self, file_contents):
        """
        Saves the extracted file contents to necessary_files_content.txt.

        Args:
            file_contents (dict): Dictionary containing file paths and their content.
        """
        output_file = "necessary_files_content.txt"

        with open(output_file, "w", encoding="utf-8") as f:
            for file_path, content in file_contents.items():
                f.write(f"\n\n--- {file_path} ---\n{content}\n")

        print(f"✅ Extracted file contents saved to {output_file}")

    def start(self, project_dir):
        print(f"🔹 Extracting project directory structure...")
        project_structure = self.extract_project_structure(project_dir)

        # Step 2: Ask LLM which files are necessary
        print(f"🔹 Asking LLM which files are needed...")
        prompt = f"""You are an AI assistant specialized in cloud infrastructure analysis.  
    Your task is to analyze a given project directory structure and determine which files are essential to identify the required AWS services for deployment.  

    ### Guidelines:
    1. Focus on files related to **application logic, configurations, infrastructure and documentation**.
    2. Identify files that define:
       - **Application Dependencies** (e.g., `package.json`, `requirements.txt`, `pom.xml`).
       - **Application Entry Points** (e.g., `server.js`, `app.py`, `main.go`).
       - **Infrastructure as Code** (e.g., Terraform files `*.tf`, CloudFormation templates).
       - **Database Schema & Configurations** (e.g., `schema.sql`, `database.yml`).
       - **Environment Variables & Secrets** (e.g., `.env`, `config.json`).
       - **Deployment & CI/CD Pipelines** (e.g., `.github/workflows/*`, `Jenkinsfile`, `Dockerfile`).
    3. Include relevant files such as README, documentation since they might contain project details and setup instructions.

    ### Input:
    Here is the extracted project structure:
    {project_structure}

    ### Task:
    From the given directory structure, list the filenames that are necessary to determine the AWS services required for deployment.  
    Return the entire filepath as same as in the provided "project structure", one per line, without explanation.
    """
        necessary_files = self.query_llm(prompt)

        # with open("necessary_files.json", "w") as f:
        #     json.dump(necessary_files_list, f, indent=4)

        print(f"\n✅ Necessary files identified")
        print(f"📄 Files Identified:", necessary_files)

        # Step 3: Extract content of necessary files
        print(f"🔹 Extracting content from {len(necessary_files)} files...")
        extracted_contents = self.extract_file_contents(necessary_files)

        self.save_extracted_content(extracted_contents)
        print("✅ Extraction process completed successfully!")


if __name__ == "__main__":
    main()

    # def main():
    #     if len(sys.argv) != 2:
    #         print("Usage: python3 extract_files.py /path/to/project")
    #         sys.exit(1)
    #
    #     project_dir = sys.argv[1]
    #
    #     # Step 1: Extract project structure
    #     print(f"🔹 Extracting project directory structure...")
    #     project_structure = extract_project_structure(project_dir)
    #
    #     # Step 2: Ask LLM which files are necessary
    #     print(f"🔹 Asking LLM which files are needed...")
    #     prompt = f"""You are an AI assistant specialized in cloud infrastructure analysis.
    # Your task is to analyze a given project directory structure and determine which files are essential to identify the required AWS services for deployment.
    #
    # ### Guidelines:
    # 1. Focus on files related to **application logic, configurations, infrastructure and documentation**.
    # 2. Identify files that define:
    #    - **Application Dependencies** (e.g., `package.json`, `requirements.txt`, `pom.xml`).
    #    - **Application Entry Points** (e.g., `server.js`, `app.py`, `main.go`).
    #    - **Infrastructure as Code** (e.g., Terraform files `*.tf`, CloudFormation templates).
    #    - **Database Schema & Configurations** (e.g., `schema.sql`, `database.yml`).
    #    - **Environment Variables & Secrets** (e.g., `.env`, `config.json`).
    #    - **Deployment & CI/CD Pipelines** (e.g., `.github/workflows/*`, `Jenkinsfile`, `Dockerfile`).
    # 3. Include relevant files such as README, documentation since they might contain project details and setup instructions.
    #
    # ### Input:
    # Here is the extracted project structure:
    # {project_structure}
    #
    # ### Task:
    # From the given directory structure, list the filenames that are necessary to determine the AWS services required for deployment.
    # Return the entire filepath as same as in the provided "project structure", one per line, without explanation.
    # """
    #     necessary_files = query_llm(prompt)


# with open("necessary_files.json", "w") as f:
#     json.dump(necessary_files_list, f, indent=4)
