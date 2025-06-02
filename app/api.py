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
    Depends,
)
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any, List
from uuid import UUID
import shutil
import tempfile
import os

from .models import (
    Document,
    DocumentCreate,
    DocumentListItem,
    DocumentListResponse,
    DocumentMetadata,
    DocumentSummary,
    DocumentEmbedding,
    SearchQuery,
    SearchResponse,
    DocumentFilters,
    FolderInfo,
    FoldersResponse,
    IngestRequest,
    IngestResponse,
    UpdateSummaryRequest,
    UpdateMetadataRequest,
    StatusResponse,
    SimilarDocumentRequest,
    SimilarDocumentsResponse,
    KeywordSearchQuery,
    KeywordSearchResponse,
    CombinedSearchQuery,
)
from .db import Database
from .paper_processor import process_pdf
from ollama import AsyncClient as OllamaAsyncClient

logger = logging.getLogger(__name__)


def get_router(db: Database, ollama_client: OllamaAsyncClient, pdf_queue=None):
    router = APIRouter()

    # IMPORTANT: Specific routes must come BEFORE parameterized routes
    # to avoid route conflicts where 'search', 'folders', etc. are interpreted as document IDs

    @router.get("/documents", response_model=DocumentListResponse)
    async def list_documents(
        skip: int = Query(0, ge=0),
        limit: int = Query(50, ge=1, le=100),
        filters: Optional[Dict[str, Any]] = None,
        folder_name: Optional[str] = None,
    ):
        response = await db.list_documents(skip, limit, folder_name, filters)
        return response

    @router.post("/documents", response_model=Document)
    async def create_document(document: DocumentCreate):
        document_id = await db.insert_document(document)
        return await db.get_document(document_id)

    # Search endpoints - must come before {document_id} routes
    @router.get("/documents/search", response_model=SearchResponse)
    async def search_documents(
        query: str = Query(..., min_length=1),
        folder_name: Optional[str] = None,
        k: int = Query(4, ge=1, le=50),
        filters: Optional[Dict[str, Any]] = None,
    ):
        results = await db.search_documents(query, folder_name, k, filters)
        return SearchResponse(
            results=results,
            query=query,
            total_results=len(results),
        )

    @router.get("/documents/search/keywords", response_model=KeywordSearchResponse)
    async def search_by_keywords(
        keywords: List[str] = Query(..., min_length=1),
        search_mode: str = Query("any", regex="^(any|all)$"),
        exact_match: bool = False,
        case_sensitive: bool = False,
        folder_name: Optional[str] = None,
        limit: int = Query(50, ge=1, le=100),
        include_snippet: bool = True,
    ):
        results = await db.search_by_keywords(
            keywords,
            search_mode,
            exact_match,
            case_sensitive,
            folder_name,
            limit,
            include_snippet,
        )
        return KeywordSearchResponse(
            results=results,
            query_keywords=keywords,
            search_mode=search_mode,
            total_results=len(results),
            exact_match=exact_match,
            case_sensitive=case_sensitive,
        )

    @router.get("/documents/search/combined", response_model=List[Dict[str, Any]])
    async def search_combined(
        text_query: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        keyword_mode: str = Query("any", regex="^(any|all)$"),
        exact_keyword_match: bool = False,
        folder_name: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = Query(20, ge=1, le=100),
        include_snippet: bool = True,
    ):
        if not text_query and not keywords:
            raise HTTPException(
                status_code=400,
                detail="Either text_query or keywords must be provided",
            )
        return await db.search_combined(
            text_query,
            keywords,
            keyword_mode,
            exact_keyword_match,
            folder_name,
            filters,
            limit,
            include_snippet,
        )

    # Folders endpoint - must come before {document_id} routes
    @router.get("/documents/folders", response_model=FoldersResponse)
    async def get_folders(base_path: Optional[str] = None):
        folders = await db.get_folders(base_path)
        return FoldersResponse(folders=folders)

    # Status endpoint - must come before {document_id} routes
    @router.get("/documents/status", response_model=StatusResponse)
    async def get_status(document_id: Optional[UUID] = None):
        status = await db.get_status(document_id)
        if document_id:
            return StatusResponse(
                total_documents=1,
                processed=1 if status == "processed" else 0,
                pending=1 if status == "pending" else 0,
                errors=1 if status == "error" else 0,
            )
        else:
            status_counts = {row["status"]: row["count"] for row in status}
            return StatusResponse(
                total_documents=sum(status_counts.values()),
                processed=status_counts.get("processed", 0),
                pending=status_counts.get("pending", 0),
                errors=status_counts.get("error", 0),
            )

    # Upload endpoint - must come before {document_id} routes
    @router.post("/documents/upload", response_model=Document)
    async def upload_paper(file: UploadFile = File(...)):
        """Upload and process a PDF document"""
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name
        try:
            paper_data = await process_pdf(tmp_path, ollama_client)
            paper_id = await db.insert_document(paper_data)
            await db.update_paper_status(paper_id, "processed")
            paper = await db.get_document(paper_id)
            return paper
        except Exception as e:
            logger.error(f"Failed to process PDF: {e}")
            raise HTTPException(status_code=500, detail="Failed to process PDF.")
        finally:
            os.unlink(tmp_path)

    # Process directory endpoint - must come before {document_id} routes
    @router.post("/documents/process-directory")
    async def process_directory(background_tasks: BackgroundTasks, directory: Optional[str] = Body(None)):
        """Process all PDFs in a directory"""
        from pathlib import Path

        dir_to_scan = directory or os.getenv("DIRECTORY", ".")
        pdfs = list(Path(dir_to_scan).rglob("*.pdf"))
        for pdf in pdfs:
            await pdf_queue.put(str(pdf))
        return JSONResponse(
            status_code=202,
            content={"message": f"Directory processing started for {dir_to_scan}"},
        )

    # NOW the parameterized routes come AFTER all specific routes
    @router.get("/documents/{document_id}", response_model=Document)
    async def get_document(document_id: UUID = Path(...)):
        document = await db.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return document

    @router.get("/documents/{document_id}/metadata", response_model=DocumentMetadata)
    async def get_document_metadata(document_id: UUID = Path(...)):
        metadata = await db.get_document_metadata(document_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="Document not found")
        return metadata

    @router.get("/documents/{document_id}/summary", response_model=DocumentSummary)
    async def get_document_summary(document_id: UUID = Path(...)):
        summary = await db.get_document_summary(document_id)
        if not summary:
            raise HTTPException(status_code=404, detail="Document not found")
        return summary

    @router.patch("/documents/{document_id}/summary", response_model=DocumentSummary)
    async def update_document_summary(
        document_id: UUID = Path(...),
        summary_data: UpdateSummaryRequest = Body(...),
    ):
        success = await db.update_document_summary(document_id, summary_data)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        return await db.get_document_summary(document_id)

    @router.patch("/documents/{document_id}/metadata", response_model=DocumentMetadata)
    async def update_document_metadata(
        document_id: UUID = Path(...),
        metadata_data: UpdateMetadataRequest = Body(...),
    ):
        success = await db.update_document_metadata(document_id, metadata_data)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        return await db.get_document_metadata(document_id)

    @router.get("/documents/{document_id}/similar", response_model=SimilarDocumentsResponse)
    async def find_similar_documents(
        document_id: UUID = Path(...),
        limit: int = Query(10, ge=1, le=50),
        threshold: float = Query(0.7, ge=0.0, le=1.0),
        title_weight: float = Query(0.75, ge=0.0, le=1.0),
        abstract_weight: float = Query(0.25, ge=0.0, le=1.0),
        include_snippet: bool = True,
        folder_name: Optional[str] = None,
    ):
        similar_docs = await db.find_similar_documents(
            document_id,
            limit,
            threshold,
            title_weight,
            abstract_weight,
            include_snippet,
            folder_name,
        )
        return SimilarDocumentsResponse(
            similar_documents=similar_docs,
            reference_document_id=document_id,
            query_weights={"title": title_weight, "abstract": abstract_weight},
            total_results=len(similar_docs),
        )

    return router
