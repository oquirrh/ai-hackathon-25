import sys

from extract_files import FileExtractor
from determine_aws_service import CodeAnalysisAgent
from terraform_gen_agent import TerraformAgent

if __name__ == '__main__':
    program_dir = sys.argv[1]
    f = FileExtractor()
    code_agent = CodeAnalysisAgent()
    t = TerraformAgent()
    f.start(program_dir)
    code_agent.start()
    t.start()

