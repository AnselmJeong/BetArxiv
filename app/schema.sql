CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS papers (
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
    title_embedding vector(768),
    abstract_embedding vector(768),
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_papers_title ON papers (title);
CREATE INDEX IF NOT EXISTS idx_papers_authors ON papers USING GIN (authors);
CREATE INDEX IF NOT EXISTS idx_papers_keywords ON papers USING GIN (keywords);
CREATE INDEX IF NOT EXISTS idx_papers_title_embedding ON papers USING hnsw (title_embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_papers_abstract_embedding ON papers USING hnsw (abstract_embedding vector_cosine_ops); 