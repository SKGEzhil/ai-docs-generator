# AI Documentation Generator 🤖📚

An intelligent FastAPI service that automatically generates comprehensive README files and API documentation from GitHub repositories using AI and RAG (Retrieval-Augmented Generation).

## ✨ Features

- 🔍 **Automatic Repository Analysis**: Analyzes GitHub repositories to understand project structure and technologies
- 📝 **README Generation**: Creates comprehensive README files with installation instructions, usage examples, and feature descriptions
- 📖 **API Documentation**: Generates detailed API documentation in Markdown and HTML formats
- 🧠 **AI-Powered**: Uses OpenAI GPT models for intelligent content generation
- 🔗 **RAG Integration**: Leverages vector databases for enhanced context understanding
- 🚀 **FastAPI Backend**: High-performance async API with automatic OpenAPI documentation

## 🛠️ Technologies Used

- **FastAPI**: Modern, fast web framework for building APIs
- **LangChain**: Framework for developing applications with language models
- **ChromaDB**: Vector database for RAG implementation
- **OpenAI GPT**: Large language models for content generation
- **PyGithub**: GitHub API integration
- **Pydantic**: Data validation and serialization

## 🚀 Installation

1. **Clone the repository**:
```bash
git clone https://github.com/SKGEzhil/ai-docs-generator
cd ai_docs
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**:
```bash
cp .env.example .env
# Edit .env with your API keys
```

4. **Configure your environment variables**:
- `OPENAI_API_KEY`: Your OpenAI API key
- `GITHUB_TOKEN`: GitHub personal access token
- Other optional configurations

## 📚 Usage

### Starting the Server

```bash
# From the project root
python -m src.main

# Or using uvicorn directly
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### API Endpoints

The service provides three main endpoints:

#### 1. Generate README
```bash
POST /generate-readme
Content-Type: application/json

{
  "repo_id": "owner/repository-name"
}
```

#### 2. Generate API Documentation (Markdown)
```bash
POST /generate-docs
Content-Type: application/json

{
  "repo_id": "owner/repository-name"
}
```

#### 3. Generate API Documentation (HTML)
```bash
POST /generate-docs-html
Content-Type: application/json

{
  "repo_id": "owner/repository-name"
}
```

### Example Usage

```python
import requests

# Generate README
response = requests.post(
    "http://localhost:8000/generate-readme",
    json={"repo_id": "facebook/react"}
)
readme_content = response.json()["content"]

# Generate API docs
response = requests.post(
    "http://localhost:8000/generate-docs",
    json={"repo_id": "fastapi/fastapi"}
)
docs_content = response.json()["content"]
```

## 🏗️ Project Structure

```
ai_docs/
├── src/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── config.py              # Configuration settings
│   ├── models.py              # Pydantic models
│   ├── github_service.py      # GitHub API integration
│   └── documentation_service.py # Documentation generation
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
└── README.md                 # This file
```

## 🔧 Configuration

The application can be configured through environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `GITHUB_TOKEN` | GitHub personal access token | Required |
| `OPENAI_MODEL` | OpenAI model to use | `gpt-4` |
| `CHUNK_SIZE` | Number of files to process per chunk | `10` |
| `MAX_RETRIES` | Maximum retries for rate limiting | `5` |

## 🌟 How It Works

1. **Repository Analysis**: The service fetches the repository structure using GitHub API
2. **File Filtering**: Intelligently filters files to focus on source code and documentation-worthy content
3. **Metadata Extraction**: Uses AI to extract detailed metadata from each file including classes, functions, and documentation
4. **RAG Indexing**: Creates a vector database index for enhanced context retrieval
5. **Content Generation**: Generates comprehensive documentation using AI with retrieved context
6. **Output Formatting**: Provides results in multiple formats (Markdown, HTML)

## 🚦 Health Check

Check the service status:
```bash
GET /health
```

## 📝 API Documentation

Once the server is running, visit:
- **Interactive API docs**: http://localhost:8000/docs
- **ReDoc documentation**: http://localhost:8000/redoc



## 🔗 Related Projects

- [LangChain](https://github.com/hwchase17/langchain)
- [FastAPI](https://github.com/tiangolo/fastapi)
- [ChromaDB](https://github.com/chroma-core/chroma)
