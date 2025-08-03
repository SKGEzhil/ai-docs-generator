import json
from typing import List, Dict, Any
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI

from .config import settings

class DocumentationService:
    """Service for generating documentation using RAG"""

    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=0.7,
            api_key=settings.OPENAI_API_KEY,
        )
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-ada-002",
            api_key=settings.OPENAI_API_KEY
        )

    def create_rag_index(self, file_objs: List[Dict[str, Any]], persist_directory: str = None) -> Chroma:
        """Create a RAG index from file metadata"""
        if persist_directory is None:
            persist_directory = settings.CHROMA_PERSIST_DIRECTORY

        documents = []

        for file_obj in file_objs:
            file_path = file_obj["path"]

            # File overview document
            file_summary = f"""
FILE_OVERVIEW: {file_path}
Module Docstring: {file_obj.get('module_docstring_or_header', 'None')}
Total Classes: {len(file_obj.get('classes', []))}
Total Functions: {len(file_obj.get('functions', []))}
Total Examples: {len(file_obj.get('examples', []))}
File Type: {file_obj.get('language', 'Unknown')}
"""
            documents.append(Document(
                page_content=file_summary,
                metadata={
                    "path": file_path,
                    "file_id": file_obj["id"],
                    "doc_type": "file_overview",
                    "full_json": json.dumps(file_obj)
                }
            ))

            # Classes document
            if file_obj.get('classes', []):
                classes_content = f"CLASSES_IN_FILE: {file_path}\n\n"
                for cls in file_obj.get('classes', []):
                    classes_content += f"""
Class: {cls['name']}
Base Classes: {cls.get('bases_or_extends', [])}
Docstring: {cls.get('docstring_or_javadoc', 'None')}
Methods: {[m['name'] for m in cls.get('methods', [])]}
"""
                documents.append(Document(
                    page_content=classes_content,
                    metadata={
                        "path": file_path,
                        "file_id": file_obj["id"],
                        "doc_type": "classes",
                        "full_json": json.dumps(file_obj)
                    }
                ))

            # Functions document
            if file_obj.get('functions', []):
                functions_content = f"FUNCTIONS_IN_FILE: {file_path}\n\n"
                for func in file_obj.get('functions', []):
                    functions_content += f"""
Function: {func['name']}
Signature: {func.get('signature', 'None')}
Decorators: {func.get('decorators_or_annotations', [])}
Return Type: {func.get('return_type', 'None')}
Docstring: {func.get('docstring_or_comment', 'None')}
Parameters: {func.get('parameters', [])}
"""
                documents.append(Document(
                    page_content=functions_content,
                    metadata={
                        "path": file_path,
                        "file_id": file_obj["id"],
                        "doc_type": "functions",
                        "full_json": json.dumps(file_obj)
                    }
                ))

            # Examples document
            if file_obj.get('examples', []):
                examples_content = f"EXAMPLES_IN_FILE: {file_path}\n\n"
                for example in file_obj.get('examples', []):
                    examples_content += f"""
Description: {example.get('description', 'None')}
Code: {example.get('code', 'None')}
"""
                documents.append(Document(
                    page_content=examples_content,
                    metadata={
                        "path": file_path,
                        "file_id": file_obj["id"],
                        "doc_type": "examples",
                        "full_json": json.dumps(file_obj)
                    }
                ))

        vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            persist_directory=persist_directory
        )
        vectorstore.persist()

        return vectorstore

    def get_all_files_from_vectorstore(self, vectorstore: Chroma, file_paths: List[str]) -> Dict[str, Any]:
        """Retrieve complete file data from vectorstore"""
        all_file_data = {}

        for file_path in file_paths:
            file_query = f"FILE_OVERVIEW: {file_path}"
            docs = vectorstore.similarity_search(file_query, k=10)

            file_docs = [doc for doc in docs if doc.metadata.get('path') == file_path]

            if file_docs:
                full_json_str = file_docs[0].metadata.get('full_json')
                if full_json_str:
                    all_file_data[file_path] = json.loads(full_json_str)

        return all_file_data

    def generate_readme(self, file_objs: List[Dict[str, Any]], vectorstore: Chroma = None) -> str:
        """Generate README documentation"""
        readme_template = {
            "system": """
You are an expert README file writer. You have been given complete JSON metadata for a codebase.

Analyze the JSON metadata and generate a comprehensive README file that includes:
1. **Project Overview**: A brief description of the project, its purpose, and main features.
2. **Installation Instructions**: Step-by-step guide on how to install and set up the project.
3. **Usage Examples**: Code snippets demonstrating how to use the main features of the project.
4. **Technologies Used**: List of major libraries or technologies used in the project.
5. **Features**: High-level features or responsibilities implemented in the project.

Use emojis to enhance the readability and engagement of the README. For example:
- Use 🚀 for installation instructions
- Use 📚 for usage examples
- Use 🛠️ for technologies used
- Use ✨ for features

Ensure the README is well-structured, easy to read, and follows best practices for documentation.
""",
            "human": "Generate the complete README now. Cover every file provided:\n\n{file_data}\n\nGenerate the documentation section now:"
        }

        return self._generate_docs_with_chunked_processing(
            file_objs, readme_template, vectorstore
        )

    def generate_api_docs(self, file_objs: List[Dict[str, Any]], vectorstore: Chroma = None) -> str:
        """Generate API documentation"""
        api_docs_template = {
            "system": """
You are an expert documentation writer. Generate a Markdown documentation section for the provided files.
Only use the information provided—do not hallucinate any endpoints, classes, functions, or parameters.

Your output should include:

1. **Module Sections**
   For each file/module:
   - **File path** (as a level‑2 heading: ## path/to/file.py)
   - Module description from docstring

2. **Classes**
   Under each module (if any):
   - Class name and base classes (level‑3 heading: ### ClassName)
   - Class description
   - Methods table:
     | Method | Signature | Return Type | Description |
     |--------|-----------|-------------|-------------|

3. **Functions**
   Under each module (if any):
   - Function name (level‑3 heading: ### function_name())
   - Function signature and description
   - Parameters table:
     | Name | Type | Default | Description |
     |------|------|---------|-------------|

4. **Examples**
   If code examples exist, include them in fenced ```python blocks under an **Examples** subsection.

Make sure your Markdown is clean and well‑formatted.
""",
            "human": "Generate documentation for these files. Cover every file provided:\n\n{file_data}\n\nGenerate the documentation section now:"
        }

        return self._generate_docs_with_chunked_processing(
            file_objs, api_docs_template, vectorstore
        )

    def generate_html_docs(self, markdown_content: str) -> str:
        """Convert markdown documentation to HTML"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """
You are an agent really good at HTML and CSS. You will be given markdown data. Your task is to convert this markdown data into a beautiful documentation page using HTML and CSS. 

Requirements:
1. Give only HTML data without any other texts
2. Include a table of contents as sidebar
3. Table of contents should have links to each file, class, and function in the documentation
4. Use modern, clean CSS styling
5. Make it responsive and professional looking
"""),
            ("human", "Convert this markdown data to HTML:\n\n{markdown_data}")
        ])

        messages = prompt.format_messages(markdown_data=markdown_content)
        result = self.llm.invoke(messages)
        return result.content

    def _generate_docs_with_chunked_processing(
        self,
        file_objs: List[Dict[str, Any]],
        prompt_templates: Dict[str, str],
        vectorstore: Chroma = None,
        chunk_size: int = None
    ) -> str:
        """Process files in chunks to handle large codebases"""
        chunk_size = chunk_size or settings.CHUNK_SIZE

        if vectorstore is None:
            try:
                vectorstore = Chroma(
                    persist_directory=settings.CHROMA_PERSIST_DIRECTORY,
                    embedding_function=self.embeddings
                )
            except Exception:
                vectorstore = self.create_rag_index(file_objs)

        file_paths = [obj["path"] for obj in file_objs]
        all_file_data = self.get_all_files_from_vectorstore(vectorstore, file_paths)

        # Add missing files from original data
        missing_files = set(file_paths) - set(all_file_data.keys())
        for file_obj in file_objs:
            if file_obj["path"] in missing_files:
                all_file_data[file_obj["path"]] = file_obj

        file_chunks = [file_paths[i:i + chunk_size] for i in range(0, len(file_paths), chunk_size)]
        documentation_parts = []

        prompt = ChatPromptTemplate.from_messages([
            ("system", prompt_templates["system"]),
            ("human", prompt_templates["human"]),
        ])

        for chunk in file_chunks:
            chunk_data = {}
            for file_path in chunk:
                if file_path in all_file_data:
                    chunk_data[file_path] = all_file_data[file_path]

            # Format file data for prompt
            formatted_data = ""
            for file_path, file_obj in chunk_data.items():
                formatted_data += f"\n--- FILE: {file_path} ---\n"
                formatted_data += f"Module Docstring: {file_obj.get('module_docstring_or_header', 'None')}\n"

                if file_obj.get('classes', []):
                    formatted_data += "Classes:\n"
                    for cls in file_obj['classes']:
                        formatted_data += f"  - {cls['name']}: {cls.get('docstring_or_javadoc', 'No description')}\n"
                        for method in cls.get('methods', []):
                            formatted_data += f"    * {method['name']}: {method.get('docstring_or_comment', 'No description')}\n"

                if file_obj.get('functions', []):
                    formatted_data += "Functions:\n"
                    for func in file_obj['functions']:
                        formatted_data += f"  - {func['name']}: {func.get('docstring_or_comment', 'No description')}\n"
                        formatted_data += f"    Signature: {func.get('signature', 'Unknown')}\n"

            messages = prompt.format_messages(file_data=formatted_data)
            result = self.llm.invoke(messages)
            documentation_parts.append(result.content)

        return "\n\n".join(documentation_parts)
