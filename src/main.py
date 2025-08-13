from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

import logging

from src.inference import Inference
from .models import GitHubRepoRequest
from src.services.github_service import GitHubService
from src.services.documentation_service import DocumentationService
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

@app.post("/generate-readme", response_class=PlainTextResponse)
async def generate_readme(request: GitHubRepoRequest):
    """
    Generate a comprehensive README file for a GitHub repository

    - **repo_id**: Repository identifier in format "owner/repo" (e.g., "facebook/react")
    """
    try:
        logger.info(f"Starting README generation for repository: {request.repo_id}")
        inference = Inference(request.repo_id)
        readme_content = inference.generate_readme()
        return readme_content

    except Exception as e:
        logger.error(f"Error generating README for {request.repo_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate README: {str(e)}"
        )

@app.post("/generate-docs", response_class=PlainTextResponse)
async def generate_docs(request: GitHubRepoRequest):
    """
    Generate comprehensive API documentation for a GitHub repository

    - **repo_id**: Repository identifier in format "owner/repo" (e.g., "facebook/react")
    """
    try:
        logger.info(f"Starting documentation generation for repository: {request.repo_id}")
        inference = Inference(request.repo_id)
        docs_content = inference.generate_docs()
        return docs_content

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

        inference = Inference(request.repo_id)
        html_content = inference.generate_html_docs()
        return html_content

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
