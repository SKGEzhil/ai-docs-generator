from src.services.github_service import GitHubService
from typing import List, Dict, Any

class Repo:
    """
    Represents a GitHub repository with methods to interact with its files and metadata.
    """

    def __init__(self, repo_id: str):
        self.repo_id = repo_id
        self.github_service = GitHubService()

        # Fetch file paths and project metadata
        self.file_paths = self.github_service.get_file_paths(self.repo_id)
        self.project_metadata = self.github_service.analyze_project_metadata(self.file_paths)

    def get_file_metadata(self) -> List[Dict[str, Any]]:
        """
        Fetches metadata for the files in the repository.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing metadata for each file.
        """

        file_metadata = self.github_service.extract_file_metadata(self.repo_id, self.file_paths, self.project_metadata)

        return file_metadata