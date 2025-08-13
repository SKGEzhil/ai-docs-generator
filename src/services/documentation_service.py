import json
from typing import List, Dict, Any
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document

from src.config import settings
from src.core.llm import llm
from src.templates import templates

class DocumentationService:
    """Service for generating documentation using RAG"""

    def __init__(self):
        self.llm = llm.get_model_info()
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-ada-002",
            api_key=settings.OPENAI_API_KEY
        )

    def create_rag_index(self, file_objs: List[Dict[str, Any]], repo_id: str) -> Chroma:
        """Create a RAG index from file metadata"""

        # Create new persist directory
        persist_directory = "./chroma_repo_index/" + repo_id

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
        readme_template = templates.readme_template

        return self._generate_docs_with_chunked_processing(
            file_objs, readme_template, vectorstore
        )

    def generate_api_docs(self, file_objs: List[Dict[str, Any]], vectorstore: Chroma = None) -> str:
        """Generate API documentation"""
        api_docs_template = templates.api_docs_template

        return self._generate_docs_with_chunked_processing(
            file_objs, api_docs_template, vectorstore
        )

    def generate_html_docs(self, markdown_content: str) -> str:
        """Convert markdown documentation to HTML"""
        html_template = templates.html_template
        prompt = ChatPromptTemplate.from_messages([
            ("system", html_template["system"]),
            ("human", html_template["human"]),
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

    def delete_rag_index(self, repo_id: str):
        """Delete the RAG index directory"""
        import shutil
        try:
            rag_path = "./chroma_repo_index/" + repo_id
            shutil.rmtree(rag_path)
            print(f"Deleted RAG index directory: {rag_path}")
        except Exception as e:
            print(f"Error deleting RAG index directory: {e}")