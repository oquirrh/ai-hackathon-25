import os
import json
import requests

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = "meta-llama/llama-3-8b-instruct:free"  # Free model


def read_project_file(file_path="necessary_files_content.txt"):
    """Reads extracted project content from file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def query_openrouter(prompt):
    """Queries OpenRouter LLM."""
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "model": OPENROUTER_MODEL,
        "messages": [{"role": "user", "content": prompt}],
    }
    response = requests.post(url, headers=headers, json=data)

    if response.status_code != 200:
        print(f"❌ API Error: {response.status_code} - {response.text}")
        sys.exit(1)

    json_response = response.json()

    # Extract the LLM-generated content
    extracted_contents = json_response["choices"][0]["message"]["content"]

    return extracted_contents


def extract_aws_services(content):
    """Uses OpenRouter LLM to determine required AWS services based on project files."""
    prompt = f"""
    Given the following project code and configurations:
    {content}
    Identify the specific AWS services required to deploy and run this application in the cloud.
    Return Only list necessary AWS services with a short justification for each.
    """
    return query_openrouter(prompt)


def main():
    print("🔍 Reading project files...")
    project_content = read_project_file()

    print("🤖 Extracting required AWS services...")
    aws_services = extract_aws_services(project_content)
    print("✅ AWS Services Required:")
    print(aws_services)

    with open("aws_services_required.txt", "w", encoding="utf-8") as f:
        f.write(aws_services)
    print("🎉 AWS service list saved as aws_services_required.txt")

    print("✅ Extraction process completed successfully!")


if __name__ == "__main__":
    main()
