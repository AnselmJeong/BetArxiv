# BetArxiv

## Research Paper Knowledge Management API

A FastAPI-based service for searching, browsing, and managing research papers stored in PostgreSQL with vector embeddings.

## Architecture Overview

**BetArxiv** is now structured with two main components:

1. **Read-Only FastAPI Service** (`backend/app/`) - Provides search, browse, and document management endpoints
2. **Batch Processing Script** (`batch_processor.py`) - Handles PDF ingestion and processing using LLMs

This separation allows for:
- A clean, focused API for frontend applications
- Independent PDF processing that can be run manually or scheduled
- Better separation of concerns between data access and data processing

## Features

- **Search and Browse**: Full-text search, keyword search, similarity search
- **Document Management**: View, update metadata and summaries
- **Folder Organization**: Browse papers by folder structure
- **Vector Embeddings**: Find similar papers using semantic similarity
- **PostgreSQL Storage**: Robust storage with pgvector for embeddings

## Quick Start

### 1. Setup Database
```bash
# Install PostgreSQL with pgvector extension
# Create database and run schema
psql -d your_db < backend/app/schema.sql
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
# Create .env file
DATABASE_URL=postgresql://user:password@localhost/betarxiv
DIRECTORY=./docs  # Directory containing PDFs for batch processing
```

### 4. Run API Server
```bash
# Start the FastAPI server
uvicorn backend.app.main:app --reload --port 8000
```

### 5. Process PDFs (Optional)
```bash
# Run batch processing to ingest PDFs
python batch_processor.py --directory ./your_pdf_directory
```

## API Documentation

### Document Management

#### List Documents
```http
GET /api/documents
```

Query Parameters:
- `skip` (int, optional): Number of documents to skip (default: 0)
- `limit` (int, optional): Maximum number of documents to return (default: 50, max: 100)
- `folder_name` (string, optional): Filter by folder name
- `filters` (object, optional): Additional filters

#### Get Document
```http
GET /api/documents/{document_id}
```

#### Get Document Summary
```http
GET /api/documents/{document_id}/summary
```

#### Get Document Metadata
```http
GET /api/documents/{document_id}/metadata
```

#### Update Document Summary
```http
PATCH /api/documents/{document_id}/summary
```

#### Update Document Metadata
```http
PATCH /api/documents/{document_id}/metadata
```

### Search Functionality

#### Semantic Search
```http
GET /api/documents/search?query=machine+learning
```

#### Similar Documents
```http
GET /api/documents/{document_id}/similar
```

#### Keyword Search
```http
GET /api/documents/search/keywords?keywords=ai&keywords=ml&search_mode=any
```

#### Combined Search
```http
GET /api/documents/search/combined?text_query=neural+networks&keywords=deep+learning
```

### Folder Management

#### List Folders
```http
GET /api/documents/folders
```

#### Get Status
```http
GET /api/documents/status
```

## Batch Processing

The `batch_processor.py` script handles PDF ingestion and processing:

```bash
# Process PDFs in a directory
python batch_processor.py --directory ./research_papers

# Process PDFs in default directory (./docs)
python batch_processor.py
```

The script will:
1. Scan for PDF files recursively
2. Check which files are already processed
3. Convert PDFs to markdown using Docling
4. Extract metadata using LLM (Ollama)
5. Generate summaries and analysis
6. Create vector embeddings
7. Store everything in PostgreSQL

## Testing

Run the test suite:

```bash
# Run all tests
pytest test_api.py -v

# Run specific test categories
pytest test_api.py::TestDatabaseSetup -v
pytest test_api.py::TestDatabaseOperations -v
```

## Development

### Project Structure
```
betarxiv/
├── backend/
│   └── app/               # FastAPI application
│       ├── main.py        # FastAPI app and startup
│       ├── api.py         # API route handlers
│       ├── db.py          # Database operations
│       ├── models.py      # Pydantic models
│       └── schema.sql     # Database schema
├── batch_processor.py     # PDF processing script
├── test_api.py           # Test suite
├── verify_setup.py       # Setup verification
└── requirements.txt      # Dependencies
```

### Key Dependencies
- **FastAPI**: Web framework for the API
- **PostgreSQL + pgvector**: Database with vector similarity
- **Ollama**: Local LLM for text processing
- **Docling**: PDF to markdown conversion
- **Pydantic**: Data validation and serialization

## Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `DIRECTORY`: Directory to scan for PDFs (batch processing only)

## License

MIT License