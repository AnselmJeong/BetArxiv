# Betarxiv

## Research Paper Knowledge Extraction API

A FastAPI-based service for extracting, summarizing, and searching research papers using LLMs, with PostgreSQL storage and directory monitoring.

## Features

-   Upload and process research papers (PDFs)
-   Extract metadata and generate summaries using LLMs (Ollama)
-   Store all data and embeddings in PostgreSQL (with pgvector)
-   Monitor a directory for new papers and process them automatically
-   Search, browse, and find similar papers via API

## API Documentation

### Document Management

#### List Documents

``` http
GET /documents
```

Query Parameters: - `skip` (int, optional): Number of documents to skip (default: 0) - `limit` (int, optional): Maximum number of documents to return (default: 50, max: 100) - `folder_name` (string, optional): Filter by folder name - `filters` (object, optional): Additional filters (e.g., year, journal)

Response:

``` json
{
    "documents": [
        {
            "id": "uuid",
            "title": "string",
            "authors": ["string"],
            "journal_name": "string",
            "year_of_publication": "integer",
            "abstract": "string",
            "folder_name": "string"
        }
    ],
    "total": "integer",
    "skip": "integer",
    "limit": "integer"
}
```

#### Get Document

``` http
GET /documents/{document_id}
```

Response: Full document details including metadata, summary, and embeddings.

#### Get Document Summary

``` http
GET /documents/{document_id}/summary
```

Response:

``` json
{
    "summary": "string",
    "distinction": "string",
    "methodology": "string",
    "results": "string",
    "implications": "string"
}
```

#### Get Document Metadata

``` http
GET /documents/{document_id}/metadata
```

Response: Document metadata including title, authors, journal, etc.

#### Update Document Summary

``` http
PUT /documents/{document_id}/update_summary
```

Request Body:

``` json
{
    "summary": "string",
    "distinction": "string",
    "methodology": "string",
    "results": "string",
    "implications": "string"
}
```

#### Update Document Metadata

``` http
PUT /documents/{document_id}/update_metadata
```

Request Body:

``` json
{
    "title": "string",
    "authors": ["string"],
    "journal_name": "string",
    "year_of_publication": "integer",
    "abstract": "string",
    "keywords": ["string"],
    "volume": "string",
    "issue": "string"
}
```

### Search Functionality

#### Semantic Search

``` http
POST /retrieve/docs
```

Request Body:

``` json
{
    "query": "string",
    "folder_name": "string",
    "k": "integer",
    "filters": {
        "year_of_publication": "integer",
        "journal_name": "string",
        "status": "string"
    }
}
```

#### Similar Documents Search

``` http
GET /documents/{document_id}/similar
```

Query Parameters: - `limit` (int, optional): Maximum results (default: 10, max: 50) - `threshold` (float, optional): Similarity threshold (default: 0.7) - `title_weight` (float, optional): Weight for title similarity (default: 0.75) - `abstract_weight` (float, optional): Weight for abstract similarity (default: 0.25) - `include_snippet` (boolean, optional): Include abstract snippets (default: true) - `folder_name` (string, optional): Filter by folder

#### Keyword Search

``` http
POST /search/keywords
```

Request Body:

``` json
{
    "keywords": ["string"],
    "search_mode": "string",  // "any" or "all"
    "exact_match": "boolean",
    "case_sensitive": "boolean",
    "limit": "integer",
    "folder_name": "string"
}
```

#### Combined Search

``` http
POST /search/combined
```

Request Body:

``` json
{
    "text_query": "string",
    "keywords": ["string"],
    "keyword_mode": "string",  // "any" or "all"
    "exact_keyword_match": "boolean",
    "folder_name": "string",
    "filters": {
        "year_of_publication": "integer",
        "journal_name": "string"
    },
    "limit": "integer",
    "include_snippet": "boolean"
}
```

### Folder Management

#### List Folders

``` http
GET /folders
```

Response:

``` json
{
    "folders": [
        {
            "name": "string",
            "path": "string",
            "document_count": "integer",
            "subfolders": ["string"]
        }
    ]
}
```

### System Status

#### Get Processing Status

``` http
GET /papers/status
```

Query Parameters: - `paper_id` (UUID, optional): Check status for specific paper

Response:

``` json
{
    "total_documents": "integer",
    "processed": "integer",
    "pending": "integer",
    "errors": "integer"
}
```

## Error Handling

The API uses standard HTTP status codes: - 200: Success - 400: Bad Request - 404: Not Found - 500: Internal Server Error

Error responses include a detail message:

``` json
{
    "detail": "Error message"
}
```

## Rate Limiting

The API implements rate limiting to prevent abuse. Current limits: - 100 requests per minute per IP - 1000 requests per hour per IP

## Authentication

Currently, the API does not implement authentication. It is recommended to: 1. Run the API behind a reverse proxy 2. Implement API key authentication 3. Use HTTPS in production

## Development

### Running Tests

``` bash
# Create test database
createdb betarxiv_test

# Install test dependencies
pip install -r requirements-test.txt

# Run tests
pytest tests/ -v
```

### API Testing

You can use the interactive API documentation at: - Swagger UI: `http://localhost:8000/docs` - ReDoc: `http://localhost:8000/redoc`