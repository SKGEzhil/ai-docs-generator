class Templates:
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

    html_docs_template = {
        "system", """
You are an agent really good at HTML and CSS. You will be given markdown data. Your task is to convert this markdown data into a beautiful documentation page using HTML and CSS. 

Requirements:
1. Give only HTML data without any other texts
2. Include a table of contents as sidebar
3. Table of contents should have links to each file, class, and function in the documentation
4. Use modern, clean CSS styling
5. Make it responsive and professional looking
""",

        "human", "Convert this markdown data to HTML:\n\n{markdown_data}"
    }

    extract_metadata_template = """
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

    project_metadata_template = """
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

    def github_response_template(self, repo_id: str):
        return {
            "input": f"Fetch the file structure of the GitHub repository and give output it as a list of python string paths "
                    f"which i can directly convert it into python list using ast.literal_eval. "
                    f"I want only the list without any other texts. repo: {repo_id}."
        }

    def github_response_filter_template(self, response: dict) -> dict:
        return {
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
        }


templates = Templates()