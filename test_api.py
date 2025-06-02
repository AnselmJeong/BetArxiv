#!/usr/bin/env python3
"""
Simplified tests for BetArxiv API - focused on database and search functionality.
No PDF processing or document creation tests.
"""

import pytest
import pytest_asyncio
import os
from uuid import UUID, uuid4
from typing import Dict, Any

from app.db import Database
from app.models import (
    DocumentCreate,
    Document,
    DocumentMetadata,
    DocumentSummary,
    UpdateSummaryRequest,
    UpdateMetadataRequest,
)

# Test database URL
TEST_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/postgres"


@pytest.mark.db
class TestDatabaseSetup:
    """Test database connection and schema setup"""

    @pytest_asyncio.fixture
    async def db(self):
        """Create a test database instance"""
        db = Database(TEST_DATABASE_URL)
        await db.connect()
        yield db
        await db.close()

    async def test_database_connection(self, db):
        """Test that database connection works"""
        assert db.pool is not None

        # Test a simple query
        async with db.pool.cursor() as cur:
            await cur.execute("SELECT 1 as test")
            result = await cur.fetchone()
            assert result["test"] == 1

    async def test_documents_table_exists(self, db):
        """Test that the documents table exists with correct schema"""
        async with db.pool.cursor() as cur:
            # Check table exists
            await cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'documents'
                )
            """)
            result = await cur.fetchone()
            assert result["exists"] is True

            # Check key columns exist
            await cur.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'documents'
                ORDER BY column_name
            """)
            columns = await cur.fetchall()
            column_names = {col["column_name"] for col in columns}

            expected_columns = {
                "id",
                "title",
                "authors",
                "journal_name",
                "publication_year",
                "abstract",
                "keywords",
                "markdown",
                "url",
                "folder_name",
                "summary",
                "distinction",
                "methodology",
                "results",
                "implications",
                "title_embedding",
                "abstract_embedding",
                "status",
                "created_at",
                "updated_at",
            }

            assert expected_columns.issubset(column_names)


@pytest.mark.unit
class TestDocumentModels:
    """Test Pydantic models for validation and serialization"""

    def test_document_create_model(self):
        """Test DocumentCreate model validation"""
        doc_data = {
            "title": "Test Paper Title",
            "authors": ["Author One", "Author Two"],
            "journal_name": "Test Journal",
            "publication_year": 2023,
            "abstract": "This is a test abstract",
            "keywords": ["test", "paper", "research"],
            "markdown": "# Test Paper\n\nContent here",
            "summary": "Test summary",
            "distinction": "Novel approach",
            "methodology": "Experimental design",
            "results": "Significant findings",
            "implications": "Important implications",
            "title_embedding": [0.1] * 768,
            "abstract_embedding": [0.2] * 768,
            "status": "processed",
            "folder_name": "test_folder",
            "url": "/path/to/test.pdf",
        }

        doc = DocumentCreate(**doc_data)
        assert doc.title == "Test Paper Title"
        assert len(doc.authors) == 2
        assert doc.publication_year == 2023
        assert len(doc.title_embedding) == 768
        assert doc.status == "processed"

    def test_document_create_minimal(self):
        """Test DocumentCreate with minimal required fields"""
        doc = DocumentCreate(title="Minimal Paper", authors=["Single Author"])
        assert doc.title == "Minimal Paper"
        assert doc.authors == ["Single Author"]
        assert doc.status == "pending"  # default
        assert doc.keywords is None

    def test_update_summary_request(self):
        """Test UpdateSummaryRequest model"""
        update_data = {
            "summary": "Updated summary",
            "methodology": "Updated methodology",
        }

        update = UpdateSummaryRequest(**update_data)
        assert update.summary == "Updated summary"
        assert update.methodology == "Updated methodology"
        assert update.distinction is None  # not provided

    def test_update_metadata_request(self):
        """Test UpdateMetadataRequest model"""
        update_data = {
            "title": "Updated Title",
            "publication_year": 2024,
            "keywords": ["updated", "keywords"],
        }

        update = UpdateMetadataRequest(**update_data)
        assert update.title == "Updated Title"
        assert update.publication_year == 2024
        assert update.keywords == ["updated", "keywords"]


@pytest.mark.db
class TestDatabaseOperations:
    """Test database CRUD operations"""

    @pytest_asyncio.fixture
    async def db(self):
        """Create a test database instance"""
        db = Database(TEST_DATABASE_URL)
        await db.connect()
        yield db
        await db.close()

    @pytest.fixture
    def sample_document(self):
        """Create a sample document for testing"""
        return DocumentCreate(
            title="Sample Research Paper",
            authors=["Dr. Test Author", "Prof. Second Author"],
            journal_name="Journal of Test Research",
            publication_year=2023,
            abstract="This is a sample abstract for testing purposes.",
            keywords=["test", "research", "sample"],
            markdown="# Sample Paper\n\nThis is the content.",
            summary="Brief summary of the paper",
            distinction="Novel testing approach",
            methodology="Controlled experiments",
            results="Positive outcomes",
            implications="Important for testing",
            title_embedding=[0.1] * 768,
            abstract_embedding=[0.2] * 768,
            status="processed",
            folder_name="test_papers",
            url="/test/sample.pdf",
        )

    async def test_insert_and_get_document(self, db, sample_document):
        """Test inserting and retrieving a document"""
        # Insert document
        document_id = await db.insert_document(sample_document)
        assert isinstance(document_id, UUID)

        # Retrieve document
        retrieved_doc = await db.get_document(document_id)
        assert retrieved_doc is not None
        assert retrieved_doc.id == document_id
        assert retrieved_doc.title == sample_document.title
        assert retrieved_doc.authors == sample_document.authors
        assert retrieved_doc.publication_year == sample_document.publication_year

        # Clean up
        await self._cleanup_document(db, document_id)

    async def test_get_nonexistent_document(self, db):
        """Test retrieving a document that doesn't exist"""
        fake_id = uuid4()
        result = await db.get_document(fake_id)
        assert result is None

    async def test_get_document_metadata(self, db, sample_document):
        """Test retrieving document metadata"""
        document_id = await db.insert_document(sample_document)

        metadata = await db.get_document_metadata(document_id)
        assert metadata is not None
        assert metadata.title == sample_document.title
        assert metadata.authors == sample_document.authors
        assert metadata.abstract == sample_document.abstract

        await self._cleanup_document(db, document_id)

    async def test_get_document_summary(self, db, sample_document):
        """Test retrieving document summary"""
        document_id = await db.insert_document(sample_document)

        summary = await db.get_document_summary(document_id)
        assert summary is not None
        assert summary.summary == sample_document.summary
        assert summary.distinction == sample_document.distinction
        assert summary.methodology == sample_document.methodology

        await self._cleanup_document(db, document_id)

    async def test_update_document_summary(self, db, sample_document):
        """Test updating document summary"""
        document_id = await db.insert_document(sample_document)

        update_data = UpdateSummaryRequest(
            summary="Updated summary content",
            methodology="Updated methodology description",
        )

        success = await db.update_document_summary(document_id, update_data)
        assert success is True

        # Verify update
        updated_summary = await db.get_document_summary(document_id)
        assert updated_summary.summary == "Updated summary content"
        assert updated_summary.methodology == "Updated methodology description"
        assert updated_summary.distinction == sample_document.distinction  # unchanged

        await self._cleanup_document(db, document_id)

    async def test_update_document_metadata(self, db, sample_document):
        """Test updating document metadata"""
        document_id = await db.insert_document(sample_document)

        update_data = UpdateMetadataRequest(
            title="Updated Paper Title",
            publication_year=2024,
            keywords=["updated", "test", "keywords"],
        )

        success = await db.update_document_metadata(document_id, update_data)
        assert success is True

        # Verify update
        updated_metadata = await db.get_document_metadata(document_id)
        assert updated_metadata.title == "Updated Paper Title"
        assert updated_metadata.publication_year == 2024
        assert updated_metadata.keywords == ["updated", "test", "keywords"]
        assert updated_metadata.authors == sample_document.authors  # unchanged

        await self._cleanup_document(db, document_id)

    async def test_list_documents(self, db):
        """Test listing documents with pagination"""
        # Insert multiple test documents
        documents = []
        for i in range(5):
            doc = DocumentCreate(
                title=f"Test Paper {i + 1}",
                authors=[f"Author {i + 1}"],
                publication_year=2020 + i,
                folder_name="test_batch",
            )
            doc_id = await db.insert_document(doc)
            documents.append(doc_id)

        # Test listing with default parameters
        result = await db.list_documents()
        assert result.total >= 5
        assert len(result.documents) >= 5

        # Test pagination
        result = await db.list_documents(skip=2, limit=2)
        assert len(result.documents) == 2
        assert result.skip == 2
        assert result.limit == 2

        # Test folder filtering
        result = await db.list_documents(folder_name="test_batch")
        assert len(result.documents) == 5

        # Clean up
        for doc_id in documents:
            await self._cleanup_document(db, doc_id)

    async def test_search_documents(self, db):
        """Test text search functionality"""
        # Insert test documents with searchable content
        doc1 = DocumentCreate(
            title="Machine Learning Algorithms",
            authors=["AI Researcher"],
            abstract="This paper discusses various machine learning algorithms including neural networks.",
            keywords=["machine learning", "algorithms", "neural networks"],
        )
        doc2 = DocumentCreate(
            title="Deep Learning Applications",
            authors=["Deep Learning Expert"],
            abstract="Applications of deep learning in computer vision and natural language processing.",
            keywords=["deep learning", "computer vision", "NLP"],
        )

        doc1_id = await db.insert_document(doc1)
        doc2_id = await db.insert_document(doc2)

        # Test search
        results = await db.search_documents("machine learning")
        assert len(results) >= 1
        assert any(r.title == "Machine Learning Algorithms" for r in results)

        # Test search with folder filter
        results = await db.search_documents("learning", folder_name="nonexistent")
        assert len(results) == 0

        # Clean up
        await self._cleanup_document(db, doc1_id)
        await self._cleanup_document(db, doc2_id)

    async def test_get_folders(self, db):
        """Test getting list of folders"""
        # Insert documents in different folders
        folders = ["ai_papers", "ml_research", "deep_learning"]
        doc_ids = []

        for folder in folders:
            doc = DocumentCreate(
                title=f"Paper in {folder}", authors=["Test Author"], folder_name=folder
            )
            doc_id = await db.insert_document(doc)
            doc_ids.append(doc_id)

        # Test getting folders
        result = await db.get_folders()
        folder_names = {f.name for f in result}
        assert all(folder in folder_names for folder in folders)

        # Clean up
        for doc_id in doc_ids:
            await self._cleanup_document(db, doc_id)

    async def test_get_status(self, db):
        """Test getting document status"""
        # Insert documents with different statuses
        doc1 = DocumentCreate(
            title="Processed Paper", authors=["Author"], status="processed"
        )
        doc2 = DocumentCreate(
            title="Pending Paper", authors=["Author"], status="pending"
        )

        doc1_id = await db.insert_document(doc1)
        doc2_id = await db.insert_document(doc2)

        # Test individual document status
        status1 = await db.get_status(doc1_id)
        assert status1 == "processed"

        status2 = await db.get_status(doc2_id)
        assert status2 == "pending"

        # Test aggregate status
        status_counts = await db.get_status()
        assert isinstance(status_counts, list)
        assert any(row["status"] == "processed" for row in status_counts)
        assert any(row["status"] == "pending" for row in status_counts)

        # Clean up
        await self._cleanup_document(db, doc1_id)
        await self._cleanup_document(db, doc2_id)

    async def _cleanup_document(self, db, document_id):
        """Helper method to clean up test documents"""
        async with db.pool.cursor() as cur:
            await cur.execute(
                "DELETE FROM documents WHERE id = %s", (str(document_id),)
            )


@pytest.mark.unit
class TestErrorHandling:
    """Test error handling and edge cases"""

    @pytest_asyncio.fixture
    async def db(self):
        """Create a test database instance"""
        db = Database(TEST_DATABASE_URL)
        await db.connect()
        yield db
        await db.close()

    async def test_database_connection_failure(self):
        """Test handling of database connection failure"""
        db = Database("postgresql://invalid:invalid@localhost:9999/invalid")
        with pytest.raises(Exception):
            await db.connect()

    async def test_invalid_document_data(self, db):
        """Test handling of invalid document data"""
        # Test with minimal valid data
        minimal_doc = DocumentCreate(title="Minimal Document", authors=["Test Author"])
        doc_id = await db.insert_document(minimal_doc)
        assert doc_id is not None

        # Clean up
        async with db.pool.cursor() as cur:
            await cur.execute("DELETE FROM documents WHERE id = %s", (str(doc_id),))

        # Test invalid field types (should raise Pydantic validation error)
        with pytest.raises(Exception):
            DocumentCreate(title=123, authors="not a list")  # type: ignore

    async def test_update_nonexistent_document(self, db):
        """Test updating a document that doesn't exist"""
        fake_id = uuid4()
        update_data = UpdateSummaryRequest(summary="New summary")

        result = await db.update_document_summary(fake_id, update_data)
        assert result is False


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
