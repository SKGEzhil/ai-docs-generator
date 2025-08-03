import requests
import json
import ast
import time
from typing import List, Dict, Any
from github import Github
from langchain_openai import ChatOpenAI
from langchain_core.tools import Tool
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from datetime import datetime

from .config import settings
from .models import FileMetadata

class GitHubService:
    """Service for interacting with GitHub API and analyzing repositories"""

    def __init__(self):
        self.github_client = Github(settings.GITHUB_TOKEN)
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=0.7,
            streaming=True,
            api_key=settings.OPENAI_API_KEY,
        )
        self._setup_tools()
        self._setup_agent()

    def _setup_tools(self):
        """Setup tools for the agent"""
        self.fetch_tool = Tool(
            name="fetch_github_repo_structure",
            func=self._fetch_repo_structure,
            description="Fetches the file structure of a GitHub repository given its owner/repo identifier."
        )

        self.get_content_tool = tool(self._get_github_content)

    def _setup_agent(self):
        """Setup the agent with tools"""
        tools = [self.fetch_tool, self.get_content_tool]

        # Create a prompt template with required agent_scratchpad variable
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant that can analyze GitHub repositories. Use the available tools to help answer questions."),
            ("human", "{input}"),
            ("human", "{agent_scratchpad}"),
        ])

        # Create agent and executor
        agent = create_openai_functions_agent(self.llm, tools, prompt)
        self.agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    def _fetch_repo_structure(self, repo: str) -> str:
        """Fetch repository file structure"""
        api_url = f"https://api.github.com/repos/{repo}"
        resp = requests.get(api_url)
        resp.raise_for_status()
        default_b = resp.json().get("default_branch", "main")

        tree_url = f"https://api.github.com/repos/{repo}/git/trees/{default_b}?recursive=1"
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

    def _get_github_content(self, repo_id: str, file: str) -> str:
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
        response = self.agent_executor.invoke({
            "input": f"Fetch the file structure of the GitHub repository and give output it as a list of python string paths "
                    f"which i can directly convert it into python list using ast.literal_eval. "
                    f"I want only the list without any other texts. repo: {repo_id}."
        })

        # Filter files for documentation
        filtered_response = self.agent_executor.invoke({
            "input": f"""
            Take the list of file paths below as input:
            file_list: {response['output']}

            Return only the list of file paths (as a Python list) that are likely to contain functions or classes that should be included in API documentation. Assume you do **not** have access to the contents of the files, and rely only on folder and filename heuristics.

            Apply these filtering rules:
            1. ✅ Include source files that likely define APIs, logic, processing, training, inference, or clients — such as files in `src/` or `server/src/`.
            2. ❌ Exclude all test files — anything under a `tests/` folder or filename starting with `test_`.
            3. ❌ Exclude deployment/configuration files — such as `.yml`, `.gitignore`, Dockerfiles, `requirements.txt`, etc.
            4. ❌ Exclude Jupyter notebooks — any `.ipynb` file.
            5. ❌ Exclude data/config folders — such as anything in `src/config/`.
            6. ❌ Exclude `__init__.py` files.

            Return only the list of included file paths in **Python list format**, with no other explanation or text.
            """
        })

        try:
            return ast.literal_eval(filtered_response['output'])
        except (ValueError, SyntaxError) as e:
            raise ValueError(f"Failed to parse file list: {e}")

    def analyze_project_metadata(self, file_list: List[str]) -> str:
        """Analyze project to infer languages, frameworks, and types"""
        project_prompt = """
        You are a project analyzer. Input: a list of file paths in a repository, provided as the variable {file_list}.

        Task:
        1. Infer what programming languages are present.
        2. Infer frameworks, runtimes, or platforms in use (e.g., FastAPI, Django, Spring Boot, Android, React, Node.js, etc.).
        3. Infer high-level project types/purposes (e.g., web backend API, mobile app, frontend SPA, library, CLI tool).
        4. Provide the key signals/evidence you used.

        Output **only** this JSON object, exactly matching this schema (no extra text):

        {{
          "languages": ["<language>", "..."],
          "frameworks": ["<framework or platform>", "..."],
          "project_types": ["<e.g., web backend>", "..."],
          "evidence": "<short explanation mentioning key files or patterns that led to these inferences>"
        }}
        """

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
        prompt_template = """
        You are a universal code metadata extractor. Input variables:
          - repo_id: {repo_id}
          - file: {file}
          - project_metadata: {project_metadata}

        First:
          * Use project_metadata to inform your heuristics.
          * Determine the language of the file from extension and context.

        Then:
          * Use the get_github_content tool to fetch the file content.

        Analyze the file thoroughly and produce **only** one JSON object matching this schema:

        {{
          "id": "<unique identifier>",
          "path": "<file path>",
          "language": "<detected language>",
          "inferred_role": "<e.g., model/entity, controller, utility, entrypoint, component, null if unclear>",
          "module_docstring_or_header": "<top-level comment or null>",
          "classes": [
            {{
              "name": "<class name>",
              "bases_or_extends": ["<base classes>"],
              "docstring_or_javadoc": "<class-level comment or null>",
              "fields": [
                {{
                  "name": "<field name>",
                  "type": "<type or null>",
                  "default": "<default value or null>",
                  "annotations_or_attributes": ["<annotations>"],
                  "visibility": "<public/private/etc. or null>",
                  "description": "<description or null>"
                }}
              ],
              "methods": [
                {{
                  "name": "<method name>",
                  "decorators_or_annotations": ["<decorators>"],
                  "signature": "<full signature>",
                  "parameters": [
                    {{
                      "name": "<param name>",
                      "type": "<type or null>",
                      "default": "<default or null>",
                      "description": "<description or null>"
                    }}
                  ],
                  "return_type": "<return type or null>",
                  "visibility": "<visibility or null>",
                  "docstring_or_comment": "<comment or null>"
                }}
              ]
            }}
          ],
          "functions": [
            {{
              "name": "<function name>",
              "decorators_or_annotations": ["<decorators>"],
              "signature": "<full signature>",
              "parameters": [
                {{
                  "name": "<param name>",
                  "type": "<type or null>",
                  "default": "<default or null>",
                  "description": "<description or null>"
                }}
              ],
              "return_type": "<return type or null>",
              "visibility": "<visibility or null>",
              "docstring_or_comment": "<comment or null>"
            }}
          ],
          "exports_or_public_api": ["<exported symbols>"],
          "examples": [
            {{
              "description": "<what the snippet illustrates>",
              "code": "<fenced code block>"
            }}
          ]
        }}
        """

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
