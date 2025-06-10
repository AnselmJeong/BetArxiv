-- Migration: Add background column to documents table
-- Date: $(date)

ALTER TABLE documents ADD COLUMN IF NOT EXISTS background TEXT;

-- Add comment for documentation
COMMENT ON COLUMN documents.background IS 'AI-generated background explanation for the document'; 