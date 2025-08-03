from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
from typing import Dict, Any
import json

from .models import GitHubRepoRequest, DocumentationResponse, ReadmeResponse, ErrorResponse
from .github_service import GitHubService
from .documentation_service import DocumentationService
from .config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI Documentation Generator",
    description="Generate README files and API documentation from GitHub repositories using AI",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
github_service = GitHubService()
doc_service = DocumentationService()

@app.on_event("startup")
async def startup_event():
    """Validate configuration on startup"""
    try:
        settings.validate()
        logger.info("Configuration validated successfully")
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "AI Documentation Generator API",
        "version": "1.0.0",
        "endpoints": {
            "generate_readme": "/generate-readme",
            "generate_docs": "/generate-docs",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        github_limits = github_service.get_github_limit()
        return {
            "status": "healthy",
            "github_api_limits": github_limits
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.post("/generate-readme", response_model=ReadmeResponse)
async def generate_readme(request: GitHubRepoRequest):
    """
    Generate a comprehensive README file for a GitHub repository

    - **repo_id**: Repository identifier in format "owner/repo" (e.g., "facebook/react")
    """
    try:
        logger.info(f"Starting README generation for repository: {request.repo_id}")

        # Step 1: Get file paths from repository
        logger.info("Fetching repository file structure...")
        file_paths = github_service.get_file_paths(request.repo_id)
        logger.info(f"Found {len(file_paths)} relevant files")

        # Step 2: Analyze project metadata
        logger.info("Analyzing project metadata...")
        project_metadata = github_service.analyze_project_metadata(file_paths)

        # Step 3: Extract file metadata
        logger.info("Extracting file metadata...")
        file_metadata = github_service.extract_file_metadata(
            request.repo_id, file_paths, project_metadata
        )

        # Step 4: Create RAG index
        logger.info("Creating RAG index...")
        vectorstore = doc_service.create_rag_index(file_metadata)

        # Step 5: Generate README
        logger.info("Generating README...")
        readme_content = doc_service.generate_readme(file_metadata, vectorstore)

        logger.info("README generation completed successfully")

        return ReadmeResponse(
            content=readme_content,
            metadata={
                "repo_id": request.repo_id,
                "files_analyzed": len(file_metadata),
                "project_metadata": json.loads(project_metadata) if project_metadata else None
            }
        )

    except Exception as e:
        logger.error(f"Error generating README for {request.repo_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate README: {str(e)}"
        )

@app.post("/generate-docs", response_model=DocumentationResponse)
async def generate_docs(request: GitHubRepoRequest):
    """
    Generate comprehensive API documentation for a GitHub repository

    - **repo_id**: Repository identifier in format "owner/repo" (e.g., "facebook/react")
    """
    try:
        logger.info(f"Starting documentation generation for repository: {request.repo_id}")

        # Step 1: Get file paths from repository
        logger.info("Fetching repository file structure...")
        file_paths = github_service.get_file_paths(request.repo_id)
        logger.info(f"Found {len(file_paths)} relevant files")

        # Step 2: Analyze project metadata
        logger.info("Analyzing project metadata...")
        project_metadata = github_service.analyze_project_metadata(file_paths)

        # Step 3: Extract file metadata
        logger.info("Extracting file metadata...")
        file_metadata = github_service.extract_file_metadata(
            request.repo_id, file_paths, project_metadata
        )

        # Step 4: Create RAG index
        logger.info("Creating RAG index...")
        vectorstore = doc_service.create_rag_index(file_metadata)

        # Step 5: Generate API documentation
        logger.info("Generating API documentation...")
        api_docs = doc_service.generate_api_docs(file_metadata, vectorstore)

        logger.info("Documentation generation completed successfully")

        return DocumentationResponse(
            content=api_docs,
            format="markdown",
            metadata={
                "repo_id": request.repo_id,
                "files_analyzed": len(file_metadata),
                "project_metadata": json.loads(project_metadata) if project_metadata else None
            }
        )

    except Exception as e:
        logger.error(f"Error generating documentation for {request.repo_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate documentation: {str(e)}"
        )

@app.post("/generate-docs-html", response_class=HTMLResponse)
async def generate_docs_html(request: GitHubRepoRequest):
    """
    Generate comprehensive API documentation for a GitHub repository in HTML format

    - **repo_id**: Repository identifier in format "owner/repo" (e.g., "facebook/react")
    """
    try:
        logger.info(f"Starting HTML documentation generation for repository: {request.repo_id}")

        # Step 1: Get file paths from repository
        logger.info("Fetching repository file structure...")
        file_paths = github_service.get_file_paths(request.repo_id)
        logger.info(f"Found {len(file_paths)} relevant files")

        # Step 2: Analyze project metadata
        logger.info("Analyzing project metadata...")
        project_metadata = github_service.analyze_project_metadata(file_paths)

        # Step 3: Extract file metadata
        logger.info("Extracting file metadata...")
        file_metadata = github_service.extract_file_metadata(
            request.repo_id, file_paths, project_metadata
        )

        # Step 4: Create RAG index
        logger.info("Creating RAG index...")
        vectorstore = doc_service.create_rag_index(file_metadata)

        # Step 5: Generate markdown documentation
        logger.info("Generating markdown documentation...")
        markdown_docs = doc_service.generate_api_docs(file_metadata, vectorstore)

        # Step 6: Convert to HTML
        logger.info("Converting to HTML...")
        html_docs = doc_service.generate_html_docs(markdown_docs)

        logger.info("HTML documentation generation completed successfully")

        return HTMLResponse(content=html_docs)

    except Exception as e:
        logger.error(f"Error generating HTML documentation for {request.repo_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate HTML documentation: {str(e)}"
        )

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return {
        "error": "Internal server error",
        "details": str(exc)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
