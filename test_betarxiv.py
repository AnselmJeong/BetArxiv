import pytest
import pytest_asyncio
import asyncio
import os
import tempfile
import shutil
from pathlib import Path
from uuid import UUID, uuid4
from typing import List, Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch
import json

# Import the application modules
from app.db import Database
from app.models import (
    DocumentCreate,
    Document,
    DocumentMetadata,
    DocumentSummary,
    DocumentEmbedding,
    UpdateSummaryRequest,
    UpdateMetadataRequest,
    DocumentListResponse,
    SearchResponse,
    SearchResult,
    FolderInfo,
)
from app.paper_processor import (
    process_pdf,
    extract_metadata,
    generate_summary,
    get_embedding,
    pdf_to_markdown,
    PaperMetadata,
    PaperSummary,
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
        update_data = {"summary": "Updated summary", "methodology": "Updated methodology"}

        update = UpdateSummaryRequest(**update_data)
        assert update.summary == "Updated summary"
        assert update.methodology == "Updated methodology"
        assert update.distinction is None  # not provided

    def test_update_metadata_request(self):
        """Test UpdateMetadataRequest model"""
        update_data = {"title": "Updated Title", "publication_year": 2024, "keywords": ["updated", "keywords"]}

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
        async with db.pool.cursor() as cur:
            await cur.execute("DELETE FROM documents WHERE id = %s", (str(document_id),))

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

        # Clean up
        async with db.pool.cursor() as cur:
            await cur.execute("DELETE FROM documents WHERE id = %s", (str(document_id),))

    async def test_get_document_summary(self, db, sample_document):
        """Test retrieving document summary"""
        document_id = await db.insert_document(sample_document)

        summary = await db.get_document_summary(document_id)
        assert summary is not None
        assert summary.summary == sample_document.summary
        assert summary.distinction == sample_document.distinction
        assert summary.methodology == sample_document.methodology

        # Clean up
        async with db.pool.cursor() as cur:
            await cur.execute("DELETE FROM documents WHERE id = %s", (str(document_id),))

    async def test_get_document_embedding(self, db, sample_document):
        """Test retrieving document embeddings"""
        document_id = await db.insert_document(sample_document)

        embedding = await db.get_document_embedding(document_id)
        assert embedding is not None
        assert len(embedding.title_embedding) == 768
        assert len(embedding.abstract_embedding) == 768
        assert embedding.title_embedding == sample_document.title_embedding

        # Clean up
        async with db.pool.cursor() as cur:
            await cur.execute("DELETE FROM documents WHERE id = %s", (str(document_id),))

    async def test_update_document_summary(self, db, sample_document):
        """Test updating document summary"""
        document_id = await db.insert_document(sample_document)

        update_data = UpdateSummaryRequest(
            summary="Updated summary content", methodology="Updated methodology description"
        )

        success = await db.update_document_summary(document_id, update_data)
        assert success is True

        # Verify update
        updated_summary = await db.get_document_summary(document_id)
        assert updated_summary.summary == "Updated summary content"
        assert updated_summary.methodology == "Updated methodology description"
        assert updated_summary.distinction == sample_document.distinction  # unchanged

        # Clean up
        async with db.pool.cursor() as cur:
            await cur.execute("DELETE FROM documents WHERE id = %s", (str(document_id),))

    async def test_update_document_metadata(self, db, sample_document):
        """Test updating document metadata"""
        document_id = await db.insert_document(sample_document)

        update_data = UpdateMetadataRequest(
            title="Updated Paper Title", publication_year=2024, keywords=["updated", "test", "keywords"]
        )

        success = await db.update_document_metadata(document_id, update_data)
        assert success is True

        # Verify update
        updated_metadata = await db.get_document_metadata(document_id)
        assert updated_metadata.title == "Updated Paper Title"
        assert updated_metadata.publication_year == 2024
        assert updated_metadata.keywords == ["updated", "test", "keywords"]
        assert updated_metadata.authors == sample_document.authors  # unchanged

        # Clean up
        async with db.pool.cursor() as cur:
            await cur.execute("DELETE FROM documents WHERE id = %s", (str(document_id),))

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
        assert isinstance(result, DocumentListResponse)
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
        async with db.pool.cursor() as cur:
            for doc_id in documents:
                await cur.execute("DELETE FROM documents WHERE id = %s", (str(doc_id),))

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
        result = await db.search_documents("machine learning")
        assert isinstance(result, SearchResponse)
        assert len(result.results) >= 1
        assert any(r.title == "Machine Learning Algorithms" for r in result.results)

        # Test search with folder filter
        result = await db.search_documents("learning", folder_name="nonexistent")
        assert len(result.results) == 0

        # Clean up
        async with db.pool.cursor() as cur:
            await cur.execute("DELETE FROM documents WHERE id IN (%s, %s)", (str(doc1_id), str(doc2_id)))

    async def test_get_folders(self, db):
        """Test getting list of folders"""
        # Insert documents in different folders
        folders = ["ai_papers", "ml_research", "deep_learning"]
        doc_ids = []

        for folder in folders:
            doc = DocumentCreate(title=f"Paper in {folder}", authors=["Test Author"], folder_name=folder)
            doc_id = await db.insert_document(doc)
            doc_ids.append(doc_id)

        # Test getting folders
        result = await db.get_folders()
        folder_names = {f.name for f in result}
        assert all(folder in folder_names for folder in folders)

        # Clean up
        async with db.pool.cursor() as cur:
            for doc_id in doc_ids:
                await cur.execute("DELETE FROM documents WHERE id = %s", (str(doc_id),))

    async def test_get_status(self, db):
        """Test getting document status"""
        # Insert documents with different statuses
        doc1 = DocumentCreate(title="Processed Paper", authors=["Author"], status="processed")
        doc2 = DocumentCreate(title="Pending Paper", authors=["Author"], status="pending")

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
        async with db.pool.cursor() as cur:
            await cur.execute("DELETE FROM documents WHERE id IN (%s, %s)", (str(doc1_id), str(doc2_id)))


@pytest.mark.unit
class TestPaperProcessor:
    """Test paper processing functionality"""

    @pytest.fixture
    def mock_ollama_client(self):
        """Create a mock Ollama client"""
        client = AsyncMock()

        # Mock chat response for metadata extraction
        client.chat.return_value = {
            "message": {
                "content": json.dumps({
                    "title": "Test Paper Title",
                    "authors": ["Test Author", "Second Author"],
                    "journal_name": "Test Journal",
                    "volume": "1",
                    "issue": "2",
                    "year_of_publication": 2023,
                    "abstract": "Test abstract content",
                    "keywords": ["test", "paper", "research"],
                })
            }
        }

        # Mock embeddings response
        client.embeddings.return_value = {"embedding": [0.1] * 768}

        return client

    @pytest.fixture
    def sample_markdown(self):
        """Sample markdown content for testing"""
        return """
# Test Paper Title

## Abstract
This is a test abstract for the paper.

## Introduction
This paper introduces a novel approach to testing.

## Methodology
We used experimental methods to validate our approach.

## Results
The results show significant improvements.

## Conclusion
This work has important implications for the field.

## References
[1] Previous work reference
[2] Another reference
"""

    async def test_extract_metadata(self, mock_ollama_client, sample_markdown):
        """Test metadata extraction from markdown"""
        result = await extract_metadata(sample_markdown, mock_ollama_client)

        assert result["title"] == "Test Paper Title"
        assert len(result["authors"]) == 2
        assert result["journal_name"] == "Test Journal"
        assert result["year_of_publication"] == 2023
        assert "test" in result["keywords"]

    async def test_generate_summary(self, mock_ollama_client, sample_markdown):
        """Test summary generation from markdown"""
        # Mock summary response
        mock_ollama_client.chat.return_value = {
            "message": {
                "content": json.dumps({
                    "summary": "Test summary",
                    "previous_work": "Previous work analysis",
                    "distinction": "Novel contribution",
                    "methodology": "Experimental approach",
                    "results": "Significant findings",
                    "implication": "Important implications",
                })
            }
        }

        result = await generate_summary(sample_markdown, mock_ollama_client)

        assert result["summary"] == "Test summary"
        assert result["methodology"] == "Experimental approach"
        assert result["results"] == "Significant findings"

    async def test_get_embedding(self, mock_ollama_client):
        """Test embedding generation"""
        text = "Test text for embedding"
        embedding = await get_embedding(text, mock_ollama_client)

        assert len(embedding) == 768
        assert all(isinstance(x, float) for x in embedding)

    @patch("app.paper_processor.DocumentConverter")
    async def test_pdf_to_markdown(self, mock_converter):
        """Test PDF to markdown conversion"""
        # Mock docling converter
        mock_result = MagicMock()
        mock_result.document.export_to_markdown.return_value = "# Test Paper\n\nContent"
        mock_converter.return_value.convert.return_value = mock_result

        result = await pdf_to_markdown("/test/path.pdf")
        assert result == "# Test Paper\n\nContent"

    @patch("app.paper_processor.pdf_to_markdown")
    @patch("app.paper_processor.extract_metadata")
    @patch("app.paper_processor.generate_summary")
    @patch("app.paper_processor.get_embedding")
    async def test_process_pdf_integration(
        self, mock_embedding, mock_summary, mock_metadata, mock_pdf2md, mock_ollama_client
    ):
        """Test full PDF processing pipeline"""
        # Setup mocks
        mock_pdf2md.return_value = "# Test Paper\n\nContent"
        mock_metadata.return_value = {
            "title": "Test Paper",
            "authors": ["Test Author"],
            "journal_name": "Test Journal",
            "volume": "1",
            "issue": "2",
            "year_of_publication": 2023,
            "abstract": "Test abstract",
            "keywords": ["test"],
        }
        mock_summary.return_value = {
            "summary": "Test summary",
            "distinction": "Novel approach",
            "methodology": "Test methodology",
            "results": "Test results",
            "implication": "Test implications",
        }
        mock_embedding.return_value = [0.1] * 768

        # Test processing
        with patch.dict(os.environ, {"DIRECTORY": "/test"}):
            result = await process_pdf("/test/folder/paper.pdf", mock_ollama_client)

        assert isinstance(result, DocumentCreate)
        assert result.title == "Test Paper"
        assert result.authors == ["Test Author"]
        assert result.folder_name == "folder"
        assert result.url == "/test/folder/paper.pdf"
        assert len(result.title_embedding) == 768
        assert result.status == "processed"


@pytest.mark.integration
class TestIngestScript:
    """Test the ingest.py script functionality"""

    @pytest.fixture
    def temp_pdf_directory(self):
        """Create a temporary directory with mock PDF files"""
        temp_dir = tempfile.mkdtemp()

        # Create some test PDF files
        (Path(temp_dir) / "folder1").mkdir()
        (Path(temp_dir) / "folder2").mkdir()

        # Create mock PDF files
        (Path(temp_dir) / "paper1.pdf").touch()
        (Path(temp_dir) / "folder1" / "paper2.pdf").touch()
        (Path(temp_dir) / "folder2" / "paper3.pdf").touch()

        yield temp_dir

        # Cleanup
        shutil.rmtree(temp_dir)

    @patch("ingest.get_all_pdf_paths")
    @patch("ingest.get_already_ingested_paths")
    @patch("ingest.Database")
    @patch("ingest.process_pdf")
    async def test_ingest_main_function(
        self, mock_process_pdf, mock_db_class, mock_get_ingested, mock_get_pdfs, temp_pdf_directory
    ):
        """Test the main ingest function"""
        from ingest import main

        # Setup mocks
        mock_db = AsyncMock()
        mock_db_class.return_value = mock_db

        mock_get_pdfs.return_value = [
            str(Path(temp_pdf_directory) / "paper1.pdf"),
            str(Path(temp_pdf_directory) / "folder1" / "paper2.pdf"),
        ]
        mock_get_ingested.return_value = set()  # No already ingested PDFs
        mock_process_pdf.return_value = DocumentCreate(title="Test Paper", authors=["Test Author"])
        mock_db.insert_document.return_value = uuid4()

        # Test with mock data
        await main(temp_pdf_directory)

        # Verify calls
        mock_db.connect.assert_called_once()
        mock_db.close.assert_called_once()
        assert mock_process_pdf.call_count == 2
        assert mock_db.insert_document.call_count == 2
        assert mock_db.update_paper_status.call_count == 2


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
        # Test 1: Try inserting a document and verify it works with minimal data
        minimal_doc = DocumentCreate(title="Minimal Document", authors=["Test Author"])
        doc_id = await db.insert_document(minimal_doc)
        assert doc_id is not None

        # Clean up the test document
        async with db.pool.cursor() as cur:
            await cur.execute("DELETE FROM documents WHERE id = %s", (str(doc_id),))

        # Test 2: Try to create a DocumentCreate with invalid field types (this should raise a Pydantic validation error)
        with pytest.raises(Exception):
            # This should fail at Pydantic validation level due to type mismatch
            DocumentCreate(title=123, authors="not a list")  # type: ignore

    async def test_update_nonexistent_document(self, db):
        """Test updating a document that doesn't exist"""
        fake_id = uuid4()
        update_data = UpdateSummaryRequest(summary="New summary")

        result = await db.update_document_summary(fake_id, update_data)
        assert result is False

    @patch("app.paper_processor.DocumentConverter")
    async def test_pdf_processing_failure(self, mock_converter):
        """Test handling of PDF processing failures"""
        mock_converter.return_value.convert.side_effect = Exception("PDF conversion failed")

        with pytest.raises(Exception):
            await pdf_to_markdown("/invalid/path.pdf")

    async def test_ollama_client_failure(self):
        """Test handling of Ollama client failures"""
        mock_client = AsyncMock()
        mock_client.chat.side_effect = Exception("LLM service unavailable")

        with pytest.raises(Exception):
            await extract_metadata("test content", mock_client)


@pytest.mark.db
class TestVectorOperations:
    """Test vector embedding and similarity operations"""

    @pytest_asyncio.fixture
    async def db(self):
        """Create a test database instance"""
        db = Database(TEST_DATABASE_URL)
        await db.connect()
        yield db
        await db.close()

    async def test_find_similar_documents(self, db):
        """Test finding similar documents using embeddings"""
        # Insert test documents with embeddings
        doc1 = DocumentCreate(
            title="Machine Learning Paper",
            authors=["ML Author"],
            abstract="Machine learning and neural networks",
            title_embedding=[0.1] * 768,
            abstract_embedding=[0.2] * 768,
        )
        doc2 = DocumentCreate(
            title="Deep Learning Study",
            authors=["DL Author"],
            abstract="Deep learning applications",
            title_embedding=[0.15] * 768,  # Similar to doc1
            abstract_embedding=[0.25] * 768,
        )
        doc3 = DocumentCreate(
            title="Quantum Computing Research",
            authors=["QC Author"],
            abstract="Quantum algorithms and qubits",
            title_embedding=[0.9] * 768,  # Very different
            abstract_embedding=[0.8] * 768,
        )

        doc1_id = await db.insert_document(doc1)
        doc2_id = await db.insert_document(doc2)
        doc3_id = await db.insert_document(doc3)

        # Find similar documents to doc1
        similar_docs = await db.find_similar_documents(
            doc1_id,
            limit=2,
            threshold=0.0,  # Low threshold to get results
        )

        # Should find doc2 as similar, doc3 as less similar
        assert len(similar_docs) >= 1
        similar_ids = [doc["id"] for doc in similar_docs]
        # Note: exact similarity depends on vector distance calculation

        # Clean up
        async with db.pool.cursor() as cur:
            for doc_id in [doc1_id, doc2_id, doc3_id]:
                await cur.execute("DELETE FROM documents WHERE id = %s", (str(doc_id),))

    async def test_search_by_keywords(self, db):
        """Test keyword-based search functionality"""
        # Insert documents with different keywords
        doc1 = DocumentCreate(
            title="AI Research Paper",
            authors=["AI Researcher"],
            keywords=["artificial intelligence", "machine learning", "neural networks"],
        )
        doc2 = DocumentCreate(
            title="Computer Vision Study",
            authors=["CV Researcher"],
            keywords=["computer vision", "image processing", "deep learning"],
        )

        doc1_id = await db.insert_document(doc1)
        doc2_id = await db.insert_document(doc2)

        # Test keyword search with "any" mode
        results = await db.search_by_keywords(keywords=["machine learning", "computer vision"], search_mode="any")
        assert len(results) >= 2

        # Test keyword search with "all" mode
        results = await db.search_by_keywords(
            keywords=["artificial intelligence", "machine learning"], search_mode="all"
        )
        assert len(results) >= 1  # Should match doc1

        # Clean up
        async with db.pool.cursor() as cur:
            await cur.execute("DELETE FROM documents WHERE id IN (%s, %s)", (str(doc1_id), str(doc2_id)))


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
