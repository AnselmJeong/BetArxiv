I'd like to change the API structure as follows.

## IMPLEMENTED API ENDPOINTS

### Retrieve documents
Search by the query

`POST /retrieve/docs`

- query: Search query text
- folder_name: Optional folder to scope the search to
- k: Number of results (default: 4)
- filters: Optional metadata filters

### List Documents
List all accessible documents

`POST /documents` (with query parameters)

- skip: number of documents to skip (default: 0)
- limit: number of documents to return (default: 50)
- filters: optional metadata filters (in request body)
- folder_name: Optional folder to scope the search to

### Get Document
Retrieve a single document by its identifier

`GET /documents/{document_id}`

- document_id: required

### Get Document Summary
Retrieve all generated summary of a single document by its identifier

`GET /documents/{document_id}/summary`

- document_id: required

### Get Document Metadata
Retrieve metadata of a single document by its identifier

Metadata includes: title, authors, journal_name, year_of_publication, abstract, keywords, volume, issue, url (filepath in the storage directory), markdown

`GET /documents/{document_id}/metadata`

- document_id: required

### Get Document Embedding
Retrieve embedding vector of a single document by its identifier

`GET /documents/{document_id}/embedding_vector`

- document_id: required

### Get Similar Documents
Find documents similar to a specific document using weighted embedding similarity

`GET /documents/{document_id}/similar`

- document_id: required
- limit: Number of results (default: 10, max: 50)
- threshold: Minimum similarity score (default: 0.7)
- title_weight: Weight for title similarity (default: 0.75 for 3:1 ratio)
- abstract_weight: Weight for abstract similarity (default: 0.25)
- include_snippet: Include abstract snippets (default: true)
- folder_name: Optional folder to limit search scope

### Search Similar Documents
Find documents similar to a search query using weighted embedding similarity

`POST /search/similar`

- Request body: SearchQuery (query, k, folder_name)
- title_weight: Weight for title similarity (default: 0.75 for 3:1 ratio)
- abstract_weight: Weight for abstract similarity (default: 0.25)
- threshold: Minimum similarity score (default: 0.7)
- include_snippet: Include abstract snippets (default: true)

### Keyword-Based Search
Search documents by specific keywords with flexible matching options

`POST /search/keywords`

- Request body: KeywordSearchQuery
  - keywords: List of keywords to search for (required)
  - search_mode: "any" (OR logic) or "all" (AND logic) (default: "any")
  - exact_match: Whether to use exact keyword matching (default: false)
  - case_sensitive: Whether search is case sensitive (default: false)
  - folder_name: Optional folder to scope search
  - limit: Maximum number of results (default: 50, max: 100)
  - include_snippet: Include abstract snippets (default: true)

### Combined Search
Search using both text queries and keywords together

`POST /search/combined`

- Request body: CombinedSearchQuery
  - text_query: Text to search in title/abstract (optional)
  - keywords: Keywords to search for (optional)
  - keyword_mode: "any" or "all" for keyword logic (default: "any")
  - exact_keyword_match: Exact keyword matching (default: false)
  - folder_name: Optional folder filter
  - filters: Additional metadata filters
  - limit: Maximum results (default: 20, max: 100)
  - include_snippet: Include snippets (default: true)

### Get All Keywords
Retrieve all unique keywords with usage statistics

`GET /keywords`

- folder_name: Optional folder to scope keywords
- limit: Maximum number of keywords to return (default: 100, max: 1000)

### Keyword Suggestions
Get keyword suggestions for autocomplete functionality

`GET /search/keywords/suggestions`

- q: Partial keyword to search for suggestions (required)
- folder_name: Optional folder to scope suggestions
- limit: Maximum number of suggestions (default: 20, max: 100)

### Update Document Summary
Update a document with new summary content

`PUT /documents/{document_id}/update_summary`

- document_id: required
- Request body: summary, distinction, methodology, results, implications (all optional)

### Update Document metadata
Update a document with new metadata

`PUT /documents/{document_id}/update_metadata`

- document_id: required
- Request body: title, authors, journal_name, year_of_publication, abstract, keywords, volume, issue, url, markdown (all optional)

### List Folders
List all the folders and subfolders

`GET /folders`

### Ingest Documents
Ingest all or newly added documents

`POST /ingest`

- folder_name: Optional folder to ingest. If None, ingest all folders
- clean_ingest: Bool (default=False). If True, re-ingest documents, if False, ingest only newly added documents

## ADDITIONAL SUGGESTIONS FOR API IMPROVEMENTS

### 1. Batch Operations
`POST /documents/batch`
- Support bulk operations for creating/updating multiple documents
- Useful for large-scale data imports

### 2. Document Collections/Tags
`GET /documents/{document_id}/collections`
`POST /documents/{document_id}/collections`
`DELETE /documents/{document_id}/collections/{collection_id}`
- Allow documents to be organized into custom collections beyond folder structure

### 3. Advanced Search
`POST /search/semantic`
- Dedicated semantic search endpoint with vector similarity
- Support for complex query combinations (AND, OR, NOT)
- Faceted search with aggregations

### 4. Document Relationships
`GET /documents/{document_id}/related`
`POST /documents/{document_id}/relationships`
- Track citations, references, and custom relationships between documents

### 5. Export Endpoints
`GET /documents/{document_id}/export?format={pdf|docx|txt|bibtex}`
- Export documents in various formats

### 6. Analytics Endpoints
`GET /analytics/overview`
`GET /analytics/folders/{folder_name}`
- Document statistics, trends, and usage analytics

### 7. Validation and Health
`GET /health`
`POST /documents/{document_id}/validate`
- System health checks and document validation

### 8. Async Operations
`GET /operations/{operation_id}`
- Track status of long-running operations like bulk ingestion

## IMPLEMENTATION NOTES

✅ All core endpoints have been implemented
✅ Database schema updated with new fields (folder_name, url)
✅ Models updated to use Document* instead of Paper* nomenclature
✅ Legacy API endpoints maintained for backward compatibility
✅ Clean schema.sql file updated for new installations

### Database Changes Made:
- Updated schema.sql with new columns and better organization
- Added comprehensive indexes for better query performance
- Added documentation comments for all fields
- Maintained backward compatibility with existing data

### Code Changes Made:
- Updated models.py with new Document* models
- Updated db.py with new document-focused methods
- Updated api.py with new REST endpoints
- Updated paper_processor.py to include folder_name and url
- Cleaned up schema.sql with new structure

### For Existing Databases:
If you have an existing database, simply run these commands to add the new columns:
```sql
ALTER TABLE papers ADD COLUMN IF NOT EXISTS folder_name TEXT;
ALTER TABLE papers ADD COLUMN IF NOT EXISTS url TEXT;
CREATE INDEX IF NOT EXISTS idx_papers_folder_name ON papers (folder_name);
```

### Next Steps:
1. Test all endpoints with real data
2. Implement semantic search using embeddings
3. Add proper error handling and validation
4. Consider implementing some of the suggested improvements
5. Update API documentation


