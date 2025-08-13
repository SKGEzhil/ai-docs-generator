import logging

from src.services.documentation_service import DocumentationService
from src.core.repo import Repo

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Inference:
    """
    A class to handle inference operations.
    """

    def __init__(self, repo_id: str):
        self.doc_service = DocumentationService()
        self.repo = Repo(repo_id)

    def generate_readme(self) -> str:
        """
        Generates a README file for the given repository.

        Returns:
            str: The generated README content.
        """
        logger.info("Generating README...")

        file_metadata = self.repo.get_file_metadata()

        # Step 4: Create RAG index
        logger.info("Creating RAG index...")
        vectorstore = self.doc_service.create_rag_index(file_metadata, self.repo.repo_id)

        # Step 5: Generate README
        logger.info("Generating README...")
        readme_content = self.doc_service.generate_readme(file_metadata, vectorstore)

        # Step 6: Clean up RAG index
        self.doc_service.delete_rag_index(self.repo.repo_id)

        logger.info("README generation completed successfully")

        return readme_content

    def generate_docs(self) -> str:
        """
        Generates comprehensive API documentation for the given repository.

        Returns:
            str: The generated documentation content.
        """
        logger.info("Generating documentation...")

        file_metadata = self.repo.get_file_metadata()

        # Step 4: Create RAG index
        logger.info("Creating RAG index...")
        vectorstore = self.doc_service.create_rag_index(file_metadata, self.repo.repo_id)

        # Step 5: Generate API documentation
        logger.info("Generating API documentation...")
        api_docs = self.doc_service.generate_api_docs(file_metadata, vectorstore)

        # Step 6: Clean up RAG index
        self.doc_service.delete_rag_index(self.repo.repo_id)

        logger.info("Documentation generation completed successfully")

        return api_docs

    def generate_html_docs(self) -> str:
        """
        Generates HTML documentation for the given repository.

        Returns:
            str: The generated HTML documentation content.
        """
        logger.info("Generating HTML documentation...")

        md_docs = self.generate_docs()
        html_docs = self.doc_service.generate_html_docs(md_docs)

        return html_docs
