-- Database schema for BetArxiv Document Management System
-- Updated for new document-based API structure

CREATE EXTENSION IF NOT EXISTS vector;

-- Main documents table (renamed from papers for clarity, but keeping 'papers' for compatibility)
CREATE TABLE IF NOT EXISTS papers (
    -- Primary identifier
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Core document metadata
    title TEXT NOT NULL,
    authors TEXT[] NOT NULL,
    journal_name TEXT,
    volume_issue TEXT,  -- Combined volume and issue for legacy compatibility
    publication_year INTEGER,
    abstract TEXT,
    keywords TEXT[],
    
    -- Document content and processing
    markdown TEXT,
    url TEXT,  -- File path to original document
    folder_name TEXT,  -- Relative folder path from base directory
    
    -- AI-generated content sections
    summary TEXT,
    previous_work TEXT,
    hypothesis TEXT,
    distinction TEXT,
    methodology TEXT,
    results TEXT,
    limitation TEXT,
    implications TEXT,
    
    -- Vector embeddings for semantic search
    title_embedding vector(768),
    abstract_embedding vector(768),
    
    -- Processing status and metadata
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_papers_title ON papers (title);
CREATE INDEX IF NOT EXISTS idx_papers_authors ON papers USING GIN (authors);
CREATE INDEX IF NOT EXISTS idx_papers_keywords ON papers USING GIN (keywords);
CREATE INDEX IF NOT EXISTS idx_papers_folder_name ON papers (folder_name);
CREATE INDEX IF NOT EXISTS idx_papers_status ON papers (status);
CREATE INDEX IF NOT EXISTS idx_papers_publication_year ON papers (publication_year);

-- Vector similarity search indexes (requires pgvector extension)
CREATE INDEX IF NOT EXISTS idx_papers_title_embedding ON papers USING hnsw (title_embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_papers_abstract_embedding ON papers USING hnsw (abstract_embedding vector_cosine_ops);

-- Add comments for documentation
COMMENT ON TABLE papers IS 'Main table storing research documents and their processed content';
COMMENT ON COLUMN papers.folder_name IS 'Folder path relative to base directory where the document is stored';
COMMENT ON COLUMN papers.url IS 'Full file path to the original document';
COMMENT ON COLUMN papers.volume_issue IS 'Combined volume and issue information (legacy field)';
COMMENT ON COLUMN papers.title_embedding IS 'Vector embedding of document title for semantic search';
COMMENT ON COLUMN papers.abstract_embedding IS 'Vector embedding of document abstract for semantic search'; 