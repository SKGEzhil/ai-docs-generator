from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class GitHubRepoRequest(BaseModel):
    """Request model for GitHub repository analysis"""
    repo_id: str = Field(..., description="Repository identifier (e.g., 'owner/repo')")

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Additional error details")

class FileMetadata(BaseModel):
    """Metadata for a file in the repository"""
    id: str
    path: str
    language: str
    inferred_role: Optional[str]
    module_docstring_or_header: Optional[str]
    classes: List[Dict[str, Any]] = []
    functions: List[Dict[str, Any]] = []
    exports_or_public_api: List[str] = []
    examples: List[Dict[str, Any]] = []
