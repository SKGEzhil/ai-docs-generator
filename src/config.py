import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    """Application configuration settings"""

    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4")
    MODEL_TEMPERATURE: float = float(os.getenv("MODEL_TEMPERATURE", "0.7"))

    # GitHub Configuration
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")

    # Vector Store Configuration
    CHROMA_PERSIST_DIRECTORY: str = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_repo_index")

    # Processing Configuration
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "10"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "5"))
    BACKOFF_SECONDS: int = int(os.getenv("BACKOFF_SECONDS", "10"))

    def validate(self):
        """Validate required configuration"""
        if not self.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required")
        if not self.GITHUB_TOKEN:
            raise ValueError("GITHUB_TOKEN is required")

settings = Settings()
