from langchain_core.tools import tool
from typing import Protocol

class GitHubServiceLike(Protocol):
    def get_github_content(self, repo_id: str, file: str) -> str: ...
    def fetch_repo_structure(self, repo_id: str) -> str: ...

class ToolRegistry:
    """
    This class provides methods to retrieve tools.
    """

    def __init__(self):
        self.tools = {}

    def get_github_tools(self, gh: GitHubServiceLike):
        @tool("get_github_content")
        def get_github_content(repo_id: str, file: str) -> str:
            """Fetch raw file text from GitHub."""
            return gh.get_github_content(repo_id, file)

        @tool("fetch_repo_structure")
        def fetch_repo_structure(repo_id: str) -> str:
            """Fetch the structure of the repository."""
            return gh.fetch_repo_structure(repo_id)

        return [get_github_content, fetch_repo_structure]

tool_registry = ToolRegistry()