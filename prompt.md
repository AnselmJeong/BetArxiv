You are an expert Python developer tasked with creating a FastAPI based API service which has the following objective:

1. For a local directory (and subdirectories) filled with downloaded research papers,

2. analyze these papers to extract important knowledge information by LLM and store them in PostgreSQL database

3. Watch the directory for newly archived papers and repeat the step 2 for these papers.

   

   The program should use modern Python (>=3.12) syntax, the `docling` package for document parsing, the `ollama-python` library for LLM tasks

   This FastAPI-based API will be integrated  with a future custom website providing the service.

**Requirements**:

1. **Directory Processing**:
   - Scan a specified directory and its subdirectories for PDF files containing research papers.
   - Process each PDF to extract information and store it in a PostgreSQL database.
2. **Background Processing**:
   - Convert each PDF to Markdown using the `docling` package (https://docling-project.github.io/docling/). 
   - Store the Markdown output into the DB
   - Use an LLM (via `ollama-python`, https://github.com/ollama/ollama-python) to extract:
     - Title
     - Authors
     - Journal name
     - Volume (Issue no.)
     - Year of publication
     - Abstract
     - Keywords
   - Use a document-processing-specialized local LLM model to generate:
     - A summary of the paper
     - Key distinction from existing work
     - Explanation of the methodology
     - Interpretation of results
     - Implications of the study
   - Store all extracted and generated data (title, authors, journal name, volume (issue no), year of publication, abstract, keywords, Markdown, summary, distinction, methodology, results, implications) in a PostgreSQL database with appropriate schema.
3. **Directory Monitoring**:
   - Use the `watchdog` library to monitor the directory for new or modified PDF files.
   - When a new PDF is detected, trigger the background processing (step 2) and update the database.
4. **Embedding Generation**:
   - Use the embedding LLM model (via `ollama`) to generate embeddings for the title and abstract of each paper.
   - Store these embeddings in the PostgreSQL database for future similarity searches (e.g., using cosine similarity).
6. **Additional Requirements**:
   - Use Python >=3.12 with modern syntax (e.g., type hints, `match` statements if applicable).
   - Use `async/await` for I/O-bound tasks (LLM calls, DB operations, file processing).
   - Design a PostgreSQL schema to store paper metadata, Markdown content, LLM-generated outputs, and embeddings (as arrays or vectors).
   - Ensure the program is modular, with separate concerns for file processing, LLM interactions, database operations, and API endpoints.
   - Handle errors gracefully (e.g., invalid PDFs, database connection issues, LLM errors) and log them using the `logging` module.
   - Provide a CLI option to specify the directory to monitor and database connection details.
   - Use Pydantic models for request/response validation.
   - Support asynchronous operations for LLM calls and database queries.
   - Include error handling for invalid PDFs, missing metadata, or LLM failures.

**Constraints**:
- Store all data, including embeddings, in PostgreSQL.
- Use the `ollama-python` library for LLM tasks, assuming Ollama is running locally with a model like `llama3.2` pulled.
- Refer to `docling` documentation for PDF-to-Markdown conversion and metadata extraction capabilities.
- Follow FastAPI’s latest reference for API implementation.

**Output Format**:

- Include comments explaining the code structure and key components.
- Provide a brief explanation of how to run the program (e.g., dependencies, environment setup, CLI usage) and write them in README.md

**Example Dependencies**:
- `docling`: For PDF parsing and Markdown conversion.
- `ollama-python`: For LLM tasks (chat and embeddings).
- `watchdog`: For directory monitoring.
- `psycopg`: For PostgreSQL interactions (use async support with `psycopg[pool]`).
- `fastapi`: For the API server.
- `uvicorn`: For running the FastAPI server.
- `pydantic`: For request/response models.
- `numpy`: For embedding similarity calculations.

**How to Run**:
- Provide instructions for setting up the environment (e.g., `pip install docling ollama fastapi uvicorn psycopg[pool] watchdog pydantic numpy`).
- Explain how to start Ollama (`ollama serve`) and pull a model (`ollama pull llama3.2`).
- Describe how to configure PostgreSQL (e.g., connection string, schema creation).
- Provide the CLI command to run the program (e.g., `python main.py --directory /path/to/papers --db-url postgresql://user:pass@localhost:5432/dbname`).
- Explain how to access the FastAPI server (e.g., `uvicorn main:app --reload` and visit `http://localhost:8000/docs`).



### Proposed API Routes and Functions
The API will provide endpoints to upload papers, retrieve processed data, and manage the processing workflow. Below is the proposed route structure, including the HTTP method, path, function, and expected behavior.

#### 1. Paper Upload and Processing
- **Route**: `POST /papers/upload`
- **Function**: Upload a single PDF file, process it (convert to Markdown, extract metadata, generate summaries), and store the results in the PostgreSQL database.
- **Request**:
  - Content: Multipart form data with a PDF file.
  - Optional query parameters: `directory` (to specify a target directory, defaults to the monitored directory).
- **Response**:
  - Success: `201 Created`, with the ID of the stored paper and basic metadata (e.g., title, authors).
  - Error: `400 Bad Request` (invalid PDF), `500 Internal Server Error` (processing or database errors).
- **Behavior**:
  - Validate the uploaded file as a PDF.
  - Use `docling` to convert the PDF to Markdown.
  - Use the LLM (via `ollama-python`) to extract title, authors, journal name, volume (issue no.), year, abstract, and keywords.
  - Use the LLM to generate summary, distinction, methodology, results, and implications.
  - Store all data in the PostgreSQL database.
  - Return the paper’s ID and metadata for confirmation.
- **Example**:
  ```json
  POST /papers/upload
  Content-Type: multipart/form-data
  Body: { file: <paper.pdf> }
  
  Response (201):
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "title": "A Study on Cancer Treatment",
    "authors": ["John Doe", "Jane Smith"],
    "status": "processed"
  }
  ```

#### 2. List All Papers
- **Route**: `GET /papers`
- **Function**: Retrieve a paginated list of all processed papers in the database.
- **Request**:
  - Query parameters:
    - `page` (default: 1): Page number for pagination.
    - `per_page` (default: 10): Number of papers per page.
    - `search` (optional): Filter by title, author, or keywords (case-insensitive).
    - `year` (optional): Filter by publication year.
- **Response**:
  - Success: `200 OK`, with a list of papers (ID, title, authors, journal, year, abstract).
  - Error: `400 Bad Request` (invalid query parameters).
- **Behavior**:
  - Query the PostgreSQL database for papers, applying filters and pagination.
  - Return a JSON array of paper metadata, with pagination metadata (e.g., total count, current page).
- **Example**:
  ```json
  GET /papers?page=1&per_page=10&search=cancer
  
  Response (200):
  {
    "papers": [
      {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "title": "A Study on Cancer Treatment",
        "authors": ["John Doe", "Jane Smith"],
        "journal": "Journal of Oncology",
        "year": 2023,
        "abstract": "This study explores..."
      },
      ...
    ],
    "pagination": {
      "page": 1,
      "per_page": 10,
      "total": 50
    }
  }
  ```

#### 3. Get Paper Details
- **Route**: `GET /papers/{id}`
- **Function**: Retrieve full details of a specific paper by its ID.
- **Request**:
  - Path parameter: `id` (UUID of the paper).
- **Response**:
  - Success: `200 OK`, with full paper details (title, authors, journal, volume, year, abstract, keywords, Markdown, summary, distinction, methodology, results, implications).
  - Error: `404 Not Found` (paper ID not found).
- **Behavior**:
  - Query the PostgreSQL database for the paper by ID.
  - Return all stored data, including LLM-generated fields.
- **Example**:
  ```json
  GET /papers/123e4567-e89b-12d3-a456-426614174000
  
  Response (200):
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "title": "A Study on Cancer Treatment",
    "authors": ["John Doe", "Jane Smith"],
    "journal": "Journal of Oncology",
    "volume": "45(3)",
    "year": 2023,
    "abstract": "This study explores...",
    "keywords": ["cancer", "treatment", "oncology"],
    "markdown": "# A Study on Cancer Treatment\n...",
    "summary": "The paper investigates...",
    "distinction": "Unlike prior work, this study...",
    "methodology": "The study employs...",
    "results": "Results show...",
    "implications": "This suggests..."
  }
  ```

#### 4. Find Similar Papers
- **Route**: `GET /papers/{id}/similar`
- **Function**: Retrieve papers with similar title/abstract embeddings, based on cosine similarity.
- **Request**:
  - Path parameter: `id` (UUID of the reference paper).
  - Query parameters:
    - `limit` (default: 5): Number of similar papers to return.
    - `threshold` (default: 0.8): Minimum cosine similarity score.
- **Response**:
  - Success: `200 OK`, with a list of similar papers (ID, title, authors, similarity score).
  - Error: `404 Not Found` (paper ID not found).
- **Behavior**:
  - Retrieve the embeddings for the title and abstract of the reference paper from the database.
  - Compute cosine similarity against other papers’ embeddings in the database.
  - Return the top `limit` papers with similarity scores above `threshold`.
- **Example**:
  ```json
  GET /papers/123e4567-e89b-12d3-a456-426614174000/similar?limit=5&threshold=0.8
  
  Response (200):
  {
    "similar_papers": [
      {
        "id": "987e6543-e21b-12d3-a456-426614174001",
        "title": "Advances in Cancer Therapy",
        "authors": ["Alice Brown"],
        "similarity_score": 0.92
      },
      ...
    ]
  }
  ```

#### 5. Trigger Directory Processing
- **Route**: `POST /papers/process-directory`
- **Function**: Trigger processing of all PDFs in the monitored directory (and subdirectories).
- **Request**:
  - Body: JSON with `directory` (optional, defaults to the configured directory).
- **Response**:
  - Success: `202 Accepted`, with a message indicating processing has started.
  - Error: `400 Bad Request` (invalid directory).
- **Behavior**:
  - Scan the specified directory (or default) for PDFs.
  - Process each PDF (as in the `POST /papers/upload` workflow) in the background.
  - Return a confirmation that processing is queued.
- **Example**:
  ```json
  POST /papers/process-directory
  Content-Type: application/json
  Body: { "directory": "/path/to/papers" }
  
  Response (202):
  {
    "message": "Directory processing started for /path/to/papers"
  }
  ```

#### 6. Get Processing Status
- **Route**: `GET /papers/status`
- **Function**: Check the status of the directory processing or individual paper processing.
- **Request**:
  - Query parameters:
    - `paper_id` (optional): Check status for a specific paper.
- **Response**:
  - Success: `200 OK`, with status details (e.g., number of papers processed, pending, or errors).
  - Error: `404 Not Found` (if `paper_id` is provided and not found).
- **Behavior**:
  - Query the database for processing status (e.g., a `status` column in the papers table).
  - If no `paper_id` is provided, return overall directory processing stats (e.g., total processed, pending).
- **Example**:
  ```json
  GET /papers/status
  
  Response (200):
  {
    "total_papers": 100,
    "processed": 90,
    "pending": 10,
    "errors": 0
  }
  ```

---

### Database Schema
To support the API, the PostgreSQL database needs a schema to store paper metadata, Markdown content, LLM-generated outputs, and embeddings. Below is a proposed schema:

```sql
CREATE TABLE papers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    authors TEXT[] NOT NULL,
    journal_name TEXT,
    volume_issue TEXT,
    publication_year INTEGER,
    abstract TEXT,
    keywords TEXT[],
    markdown TEXT,
    summary TEXT,
    distinction TEXT,
    methodology TEXT,
    results TEXT,
    implications TEXT,
    title_embedding VECTOR(768), -- Adjust dimension based on LLM model
    abstract_embedding VECTOR(768),
    status VARCHAR(20) DEFAULT 'pending', -- e.g., 'pending', 'processed', 'error'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_papers_title ON papers (title);
CREATE INDEX idx_papers_authors ON papers USING GIN (authors);
CREATE INDEX idx_papers_keywords ON papers USING GIN (keywords);
CREATE INDEX idx_papers_title_embedding ON papers USING hnsw (title_embedding vector_cosine_ops);
CREATE INDEX idx_papers_abstract_embedding ON papers USING hnsw (abstract_embedding vector_cosine_ops);
```

- **Notes**:
  - The `VECTOR` type assumes the `pgvector` extension for PostgreSQL to store and query embeddings efficiently.
  - Indexes improve query performance for searches and similarity calculations.
  - The `status` column tracks processing state for the `/papers/status` endpoint.

---

### Directory Monitoring
- **Implementation**: Use the `watchdog` library to monitor the specified directory for new or modified PDFs.
- **Behavior**: When a new PDF is detected, queue it for processing (same workflow as `POST /papers/upload`) in the background.
- **Integration with FastAPI**: Run the directory watcher as a background task, started when the FastAPI app initializes (using FastAPI’s `lifespan` event handler).

---

### Example Workflow for the Website
1. **User Uploads a Paper or papers**:
   - The frontend sends a PDF to `POST /papers/upload`.
   - The API processes the PDF, stores the results, and returns the paper ID.
   - The frontend displays a confirmation with the paper’s title and authors.

2. **User Browses Papers**:
   - The frontend calls `GET /papers?search=cancer&page=1` to display a list of papers.
   - The user clicks a paper to view details, triggering `GET /papers/{id}`.

3. **User Explores Similar Papers**:
   - The frontend calls `GET /papers/{id}/similar` to show related papers based on embeddings.

4. **Automated Processing**:
   - The backend monitors the directory and processes new PDFs automatically.
   - The frontend can check progress via `GET /papers/status`.

---

Please generate the complete program according to these specifications, ensuring all components (directory processing, background tasks, directory monitoring, embedding generation, and FastAPI endpoints) are implemented correctly.