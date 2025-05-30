import logging
from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException,
    BackgroundTasks,
    Query,
    Body,
    Path,
)
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
from uuid import UUID
import shutil
import tempfile
import os

from .models import (
    Document,
    DocumentListResponse,
    DocumentMetadata,
    DocumentSummary,
    DocumentEmbedding,
    SearchQuery,
    SearchResponse,
    DocumentFilters,
    FoldersResponse,
    IngestRequest,
    IngestResponse,
    UpdateSummaryRequest,
    UpdateMetadataRequest,
    StatusResponse,
    SimilarDocumentRequest,
    SimilarDocument,
    SimilarDocumentsResponse,
    KeywordSearchQuery,
    KeywordSearchResult,
    KeywordSearchResponse,
    CombinedSearchQuery,
    # Legacy models for backward compatibility
    Paper,
    PaperListResponse,
    SimilarPapersResponse,
)
from .db import Database
from .paper_processor import process_pdf
from ollama import AsyncClient as OllamaAsyncClient

logger = logging.getLogger(__name__)


def get_router(db: Database, ollama_client: OllamaAsyncClient, pdf_queue):
    router = APIRouter()

    # === NEW API ENDPOINTS ===

    @router.post("/retrieve/docs", response_model=SearchResponse)
    async def retrieve_documents(search_query: SearchQuery):
        """Search documents by query with optional filters"""
        results = await db.search_documents(
            query=search_query.query,
            folder_name=search_query.folder_name,
            k=search_query.k,
            filters=search_query.filters,
        )
        return SearchResponse(
            results=results, query=search_query.query, total_results=len(results)
        )

    @router.post("/documents", response_model=DocumentListResponse)
    async def list_documents(
        skip: int = Query(0, ge=0),
        limit: int = Query(50, ge=1, le=100),
        folder_name: Optional[str] = Query(None),
        filters: Optional[Dict[str, Any]] = Body(None),
    ):
        """List all accessible documents with pagination and filtering"""
        documents, total = await db.list_documents(
            skip=skip, limit=limit, filters=filters, folder_name=folder_name
        )
        return DocumentListResponse(
            documents=documents, total=total, skip=skip, limit=limit
        )

    @router.get("/documents/{document_id}", response_model=Document)
    async def get_document(document_id: UUID = Path(...)):
        """Retrieve a single document by its identifier"""
        document = await db.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return document

    @router.get("/documents/{document_id}/summary", response_model=DocumentSummary)
    async def get_document_summary(document_id: UUID = Path(...)):
        """Retrieve all generated summary of a single document by its identifier"""
        summary = await db.get_document_summary(document_id)
        if not summary:
            raise HTTPException(
                status_code=404, detail="Document not found or no summary available"
            )
        return summary

    @router.get("/documents/{document_id}/metadata", response_model=DocumentMetadata)
    async def get_document_metadata(document_id: UUID = Path(...)):
        """Retrieve metadata of a single document by its identifier"""
        metadata = await db.get_document_metadata(document_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="Document not found")
        return metadata

    @router.get(
        "/documents/{document_id}/embedding_vector", response_model=DocumentEmbedding
    )
    async def get_document_embedding(document_id: UUID = Path(...)):
        """Retrieve embedding vector of a single document by its identifier"""
        embedding = await db.get_document_embedding(document_id)
        if not embedding:
            raise HTTPException(
                status_code=404, detail="Document not found or no embedding available"
            )
        return embedding

    @router.put("/documents/{document_id}/update_summary")
    async def update_document_summary(
        document_id: UUID = Path(...), summary_data: UpdateSummaryRequest = Body(...)
    ):
        """Update a document with new summary content"""
        updated = await db.update_document_summary(document_id, summary_data)
        if not updated:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"message": "Summary updated successfully", "document_id": document_id}

    @router.put("/documents/{document_id}/update_metadata")
    async def update_document_metadata(
        document_id: UUID = Path(...), metadata_data: UpdateMetadataRequest = Body(...)
    ):
        """Update a document with new metadata"""
        updated = await db.update_document_metadata(document_id, metadata_data)
        if not updated:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"message": "Metadata updated successfully", "document_id": document_id}

    @router.get("/folders", response_model=FoldersResponse)
    async def list_folders():
        """List all the folders and subfolders"""
        folders = await db.get_folders()
        return FoldersResponse(folders=folders)

    @router.get(
        "/documents/{document_id}/similar", response_model=SimilarDocumentsResponse
    )
    async def get_similar_documents(
        document_id: UUID = Path(...),
        limit: int = Query(10, ge=1, le=50),
        threshold: float = Query(0.7, ge=0.0, le=1.0),
        title_weight: float = Query(
            0.75,
            ge=0.0,
            le=1.0,
            description="Weight for title similarity (default 0.75 for 3:1 ratio)",
        ),
        abstract_weight: float = Query(
            0.25,
            ge=0.0,
            le=1.0,
            description="Weight for abstract similarity (default 0.25)",
        ),
        include_snippet: bool = Query(
            True, description="Include abstract snippets in results"
        ),
        folder_name: Optional[str] = Query(
            None, description="Limit search to specific folder"
        ),
    ):
        """
        Find documents similar to the given document using weighted embedding similarity.

        Uses cosine similarity on both title and abstract embeddings with customizable weights.
        Default weights are 0.75 for title and 0.25 for abstract (3:1 ratio).
        """
        results = await db.find_similar_documents(
            document_id=document_id,
            limit=limit,
            threshold=threshold,
            title_weight=title_weight,
            abstract_weight=abstract_weight,
            include_snippet=include_snippet,
            folder_name=folder_name,
        )

        similar_docs = [
            SimilarDocument(
                id=r["id"],
                title=r["title"],
                authors=r["authors"],
                similarity_score=r["similarity_score"],
                title_similarity=r["title_similarity"],
                abstract_similarity=r["abstract_similarity"],
                snippet=r["snippet"],
                folder_name=r["folder_name"],
            )
            for r in results
        ]

        # Normalize weights for response
        total_weight = title_weight + abstract_weight
        if total_weight > 0:
            norm_title_weight = title_weight / total_weight
            norm_abstract_weight = abstract_weight / total_weight
        else:
            norm_title_weight = norm_abstract_weight = 0.5

        return SimilarDocumentsResponse(
            similar_documents=similar_docs,
            reference_document_id=document_id,
            query_weights={
                "title_weight": norm_title_weight,
                "abstract_weight": norm_abstract_weight,
            },
            total_results=len(similar_docs),
        )

    @router.post("/search/similar", response_model=SimilarDocumentsResponse)
    async def search_similar_documents(
        search_query: SearchQuery,
        title_weight: float = Query(0.75, ge=0.0, le=1.0),
        abstract_weight: float = Query(0.25, ge=0.0, le=1.0),
        threshold: float = Query(0.7, ge=0.0, le=1.0),
        include_snippet: bool = Query(True),
    ):
        """
        Find documents similar to a search query using weighted embedding similarity.

        Generates embeddings for the search query and finds similar documents.
        Uses 3:1 ratio for title:abstract weights by default.
        """
        from .paper_processor import get_embedding

        # Generate embeddings for the search query
        try:
            # Use the query as both title and abstract for embedding generation
            title_embedding = await get_embedding(search_query.query, ollama_client)
            abstract_embedding = await get_embedding(search_query.query, ollama_client)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate embeddings for search query: {e}",
            )

        results = await db.find_similar_documents_by_embeddings(
            title_embedding=title_embedding,
            abstract_embedding=abstract_embedding,
            limit=search_query.k,
            threshold=threshold,
            title_weight=title_weight,
            abstract_weight=abstract_weight,
            include_snippet=include_snippet,
            folder_name=search_query.folder_name,
        )

        similar_docs = [
            SimilarDocument(
                id=r["id"],
                title=r["title"],
                authors=r["authors"],
                similarity_score=r["similarity_score"],
                title_similarity=r["title_similarity"],
                abstract_similarity=r["abstract_similarity"],
                snippet=r["snippet"],
                folder_name=r["folder_name"],
            )
            for r in results
        ]

        # Normalize weights for response
        total_weight = title_weight + abstract_weight
        if total_weight > 0:
            norm_title_weight = title_weight / total_weight
            norm_abstract_weight = abstract_weight / total_weight
        else:
            norm_title_weight = norm_abstract_weight = 0.5

        return SimilarDocumentsResponse(
            similar_documents=similar_docs,
            reference_document_id=None,  # No reference document for search-based similarity
            query_weights={
                "title_weight": norm_title_weight,
                "abstract_weight": norm_abstract_weight,
                "search_query": search_query.query,
            },
            total_results=len(similar_docs),
        )

    @router.post("/search/keywords", response_model=KeywordSearchResponse)
    async def search_by_keywords(search_query: KeywordSearchQuery):
        """
        Search documents by keywords with flexible matching options.

        Supports exact/fuzzy matching, AND/OR logic, case sensitivity, and folder filtering.
        Returns match scores based on the percentage of keywords matched.
        """
        results = await db.search_by_keywords(
            keywords=search_query.keywords,
            search_mode=search_query.search_mode,
            exact_match=search_query.exact_match,
            case_sensitive=search_query.case_sensitive,
            folder_name=search_query.folder_name,
            limit=search_query.limit,
            include_snippet=search_query.include_snippet,
        )

        keyword_results = [
            KeywordSearchResult(
                id=r["id"],
                title=r["title"],
                authors=r["authors"],
                keywords=r["keywords"],
                matched_keywords=r["matched_keywords"],
                match_score=r["match_score"],
                snippet=r["snippet"],
                folder_name=r["folder_name"],
                abstract=r["abstract"],
            )
            for r in results
        ]

        return KeywordSearchResponse(
            results=keyword_results,
            query_keywords=search_query.keywords,
            search_mode=search_query.search_mode,
            total_results=len(keyword_results),
            exact_match=search_query.exact_match,
            case_sensitive=search_query.case_sensitive,
        )

    @router.post("/search/combined")
    async def search_combined(search_query: CombinedSearchQuery):
        """
        Combined search using both text queries and keywords.

        Allows searching in title/abstract text while also filtering by keywords.
        Supports flexible keyword matching and additional metadata filters.
        """
        if not search_query.text_query and not search_query.keywords:
            raise HTTPException(
                status_code=400, detail="Either text_query or keywords must be provided"
            )

        results = await db.search_combined(
            text_query=search_query.text_query,
            keywords=search_query.keywords,
            keyword_mode=search_query.keyword_mode,
            exact_keyword_match=search_query.exact_keyword_match,
            folder_name=search_query.folder_name,
            filters=search_query.filters,
            limit=search_query.limit,
            include_snippet=search_query.include_snippet,
        )

        # Return in SearchResponse format for compatibility
        search_results = [
            SearchResult(
                id=r["id"],
                title=r["title"],
                authors=r["authors"],
                similarity_score=r["relevance_score"],
                snippet=r["snippet"],
            )
            for r in results
        ]

        query_description = []
        if search_query.text_query:
            query_description.append(f"text: '{search_query.text_query}'")
        if search_query.keywords:
            query_description.append(
                f"keywords: {search_query.keywords} ({search_query.keyword_mode})"
            )

        return SearchResponse(
            results=search_results,
            query=" + ".join(query_description),
            total_results=len(search_results),
        )

    @router.get("/keywords")
    async def get_all_keywords(
        folder_name: Optional[str] = Query(
            None, description="Optional folder to scope keywords"
        ),
        limit: int = Query(
            100, ge=1, le=1000, description="Maximum number of keywords to return"
        ),
    ):
        """
        Get all unique keywords from documents with usage statistics.

        Returns keywords sorted by usage frequency with counts of how many
        documents and folders use each keyword.
        """
        keywords = await db.get_all_keywords(folder_name=folder_name)

        # Limit results
        limited_keywords = keywords[:limit]

        return {
            "keywords": limited_keywords,
            "total_unique_keywords": len(keywords),
            "returned_count": len(limited_keywords),
            "folder_filter": folder_name,
        }

    @router.get("/search/keywords/suggestions")
    async def get_keyword_suggestions(
        q: str = Query(..., description="Partial keyword to search for suggestions"),
        folder_name: Optional[str] = Query(
            None, description="Optional folder to scope suggestions"
        ),
        limit: int = Query(
            20, ge=1, le=100, description="Maximum number of suggestions"
        ),
    ):
        """
        Get keyword suggestions based on a partial match.

        Useful for autocomplete functionality in search interfaces.
        """
        # Get all keywords and filter by partial match
        all_keywords = await db.get_all_keywords(folder_name=folder_name)

        # Filter keywords that contain the query string (case insensitive)
        q_lower = q.lower()
        suggestions = [kw for kw in all_keywords if q_lower in kw["keyword"].lower()]

        # Sort by usage count (most used first) and limit
        suggestions.sort(key=lambda x: x["usage_count"], reverse=True)
        limited_suggestions = suggestions[:limit]

        return {
            "suggestions": limited_suggestions,
            "query": q,
            "total_matches": len(suggestions),
            "returned_count": len(limited_suggestions),
            "folder_filter": folder_name,
        }

    # === LEGACY API ENDPOINTS (for backward compatibility) ===

    @router.post("/papers/upload", response_model=Paper)
    async def upload_paper(file: UploadFile = File(...)):
        """Legacy endpoint for uploading papers"""
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name
        try:
            paper_data = await process_pdf(tmp_path, ollama_client)
            paper_id = await db.insert_paper(paper_data)
            await db.update_paper_status(paper_id, "processed")
            paper = await db.get_paper(paper_id)
            return paper
        except Exception as e:
            logger.error(f"Failed to process PDF: {e}")
            raise HTTPException(status_code=500, detail="Failed to process PDF.")
        finally:
            os.unlink(tmp_path)

    @router.get("/papers", response_model=PaperListResponse)
    async def list_papers(
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=100),
        search: Optional[str] = None,
        year: Optional[int] = None,
    ):
        """Legacy endpoint for listing papers"""
        papers, total = await db.list_papers(page, per_page, search, year)
        return PaperListResponse(
            papers=papers,
            pagination={"page": page, "per_page": per_page, "total": total},
        )

    @router.get("/papers/{id}", response_model=Paper)
    async def get_paper(id: UUID):
        """Legacy endpoint for getting a paper"""
        paper = await db.get_paper(id)
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found.")
        return paper

    @router.get("/papers/{id}/similar", response_model=SimilarPapersResponse)
    async def similar_papers(
        id: UUID,
        limit: int = Query(5, ge=1, le=20),
        threshold: float = Query(0.8, ge=0.0, le=1.0),
    ):
        """Legacy endpoint for finding similar papers"""
        results = await db.get_similar_papers(id, limit, threshold)
        return SimilarPapersResponse(similar_papers=results)

    @router.post("/papers/process-directory")
    async def process_directory(
        background_tasks: BackgroundTasks, directory: Optional[str] = Body(None)
    ):
        """Legacy endpoint for processing directory"""
        from pathlib import Path

        dir_to_scan = directory or os.getenv("DIRECTORY", ".")
        pdfs = list(Path(dir_to_scan).rglob("*.pdf"))
        for pdf in pdfs:
            await pdf_queue.put(str(pdf))
        return JSONResponse(
            status_code=202,
            content={"message": f"Directory processing started for {dir_to_scan}"},
        )

    @router.get("/papers/status", response_model=StatusResponse)
    async def get_status(paper_id: Optional[UUID] = None):
        """Legacy endpoint for getting status"""
        status = await db.get_status(paper_id)
        if not status:
            raise HTTPException(status_code=404, detail="Not found.")
        return status

    return router
