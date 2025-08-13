import requests
import json
import ast
import time
from typing import List, Dict, Any
from github import Github
from langchain_core.prompts import ChatPromptTemplate
from datetime import datetime

from src.core.agent import Agent
from src.config import settings
from src.core.llm import llm
from src.core.tool_registry import tool_registry
from src.templates import templates

class GitHubService:
    """Service for interacting with GitHub API and analyzing repositories"""

    def __init__(self):
        self.github_client = Github(settings.GITHUB_TOKEN)
        self.llm = llm.get_model_info()
        self._setup_agent()

    def _setup_agent(self):
        """Setup the agent with tools"""
        tools = tool_registry.get_github_tools(self)

        # Create a prompt template with required agent_scratchpad variable
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant that can analyze GitHub repositories. Use the available tools to help answer questions."),
            ("human", "{input}"),
            ("human", "{agent_scratchpad}"),
        ])

        self.agent_executor = Agent(tools, prompt).get_agent_executor()

    def fetch_repo_structure(self, repo_id: str) -> str:
        """
        Fetch repository file structure

        Args:
            repo_id: The identifier of the GitHub repository (e.g. "owner/repo").

        """
        api_url = f"https://api.github.com/repos/{repo_id}"
        resp = requests.get(api_url)
        resp.raise_for_status()
        default_b = resp.json().get("default_branch", "main")

        tree_url = f"https://api.github.com/repos/{repo_id}/git/trees/{default_b}?recursive=1"
        resp = requests.get(tree_url)
        resp.raise_for_status()
        tree = resp.json().get("tree", [])

        structure = {}
        for item in tree:
            parts = item["path"].split("/")
            d = structure
            for part in parts:
                d = d.setdefault(part, {})

        def format_tree(node, prefix=""):
            lines = []
            for name, subtree in sorted(node.items()):
                lines.append(f"{prefix}{name}")
                if subtree:
                    lines.extend(format_tree(subtree, prefix + "    "))
            return lines

        return "\n".join(format_tree(structure))

    def get_github_content(self, repo_id: str, file: str) -> str:
        """
        Fetches the content of a file in a GitHub repository.

        Args:
            repo_id: The identifier of the GitHub repository (e.g. "owner/repo").
            file: Path to the file within the repo.
        """
        repo = self.github_client.get_repo(repo_id)
        blob = repo.get_contents(file, ref="main")
        return blob.decoded_content.decode("utf-8")

    def get_github_limit(self) -> Dict[str, Any]:
        """Returns the current GitHub API rate limit status"""
        limits = self.github_client.get_rate_limit().core
        return {
            "limit": limits.limit,
            "remaining": limits.remaining,
            "reset": datetime.fromtimestamp(limits.reset.timestamp())
        }

    def get_file_paths(self, repo_id: str) -> List[str]:
        """Get filtered file paths from repository"""
        response = self.agent_executor.invoke(templates.github_response_template(repo_id))

        # Filter files for documentation
        filtered_response = self.agent_executor.invoke(templates.github_response_filter_template(response))

        try:
            return ast.literal_eval(filtered_response['output'])
        except (ValueError, SyntaxError) as e:
            raise ValueError(f"Failed to parse file list: {e}")

    def analyze_project_metadata(self, file_list: List[str]) -> str:
        """Analyze project to infer languages, frameworks, and types"""
        project_prompt = templates.project_metadata_template

        result = self.agent_executor.invoke({
            "input": project_prompt.format(file_list=file_list)
        })
        return result['output']

    def safe_run(self, prompt: str, max_retries: int = None, backoff_secs: int = None) -> str:
        """Run agent with retry logic for rate limiting"""
        max_retries = max_retries or settings.MAX_RETRIES
        backoff_secs = backoff_secs or settings.BACKOFF_SECONDS

        for attempt in range(1, max_retries + 1):
            try:
                result = self.agent_executor.invoke({"input": prompt})
                return result['output']
            except Exception as e:
                text = str(e)
                if '429' in text or 'rate limit' in text.lower():
                    wait = backoff_secs * (2 ** (attempt - 1))
                    print(f"[{attempt}/{max_retries}] Rate limit hit; sleeping {wait}s…")
                    time.sleep(wait)
                else:
                    raise

        raise RuntimeError(f"Failed after {max_retries} rate-limit retries")

    def extract_file_metadata(self, repo_id: str, file_list: List[str], project_metadata: str) -> List[Dict[str, Any]]:
        """Extract metadata from each file in the repository"""
        prompt_template = templates.extract_metadata_template

        data_list = []
        for item in file_list:
            raw = self.safe_run(prompt_template.format(
                repo_id=repo_id,
                file=item,
                project_metadata=project_metadata
            ))

            try:
                obj = json.loads(raw)
            except json.JSONDecodeError:
                obj = {"error_parsing_JSON": raw, "path": item, "id": item}

            data_list.append(obj)

        return data_list
