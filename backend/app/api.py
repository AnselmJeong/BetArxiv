import logging
import os
from pathlib import Path
from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    Body,
    Path as FastAPIPath,
)
from fastapi.responses import FileResponse, StreamingResponse
from typing import Optional, Dict, Any, List
from uuid import UUID
import io
from PIL import Image

from .models import (
    Document,
    DocumentListResponse,
    DocumentMetadata,
    DocumentSummary,
    FoldersResponse,
    UpdateSummaryRequest,
    UpdateMetadataRequest,
    StatusResponse,
    SimilarDocumentsResponse,
    KeywordSearchResponse,
    SearchResponse,
    SearchResult,
    ChatRequest,
    ChatResponse,
    ChatMessage,
    UpdateRatingRequest,
)
from .db import Database

logger = logging.getLogger(__name__)


def get_router(db: Database):
    router = APIRouter()

    # PDF serving endpoint - must come before other routes to avoid conflicts
    @router.get("/api/pdf")
    async def serve_pdf(
        path: str = Query(..., description="Relative path to the PDF file"),
        base_dir: str = Query(
            default="docs", description="Base directory for PDF files"
        ),
    ):
        """Serve PDF files from the local file system."""
        try:
            # Use the provided base directory or fallback to default
            base_directory = Path(base_dir).resolve()

            # Handle path - assume it's always relative to base directory
            relative_path = Path(path)

            # Construct absolute path
            pdf_path = (base_directory / relative_path).resolve()

            logger.info(f"Base directory: {base_directory}")
            logger.info(f"Relative path: {relative_path}")
            logger.info(f"Attempting to serve PDF: {pdf_path}")

            # Security check: ensure the resolved path is still within base directory
            try:
                pdf_path.relative_to(base_directory.resolve())
            except ValueError:
                logger.error(
                    f"Security violation: path outside base directory: {pdf_path}"
                )
                raise HTTPException(
                    status_code=403,
                    detail="Access to path outside base directory denied",
                )

            # Validation checks
            if not pdf_path.exists():
                logger.error(f"PDF file not found: {pdf_path}")
                raise HTTPException(
                    status_code=404, detail=f"PDF file not found: {path}"
                )

            if not pdf_path.is_file():
                logger.error(f"Path is not a file: {pdf_path}")
                raise HTTPException(status_code=400, detail="Path is not a file")

            if pdf_path.suffix.lower() != ".pdf":
                logger.error(f"File is not a PDF: {pdf_path}")
                raise HTTPException(status_code=400, detail="File is not a PDF")

            # Additional security: ensure file is readable
            if not os.access(pdf_path, os.R_OK):
                logger.error(f"PDF file not readable: {pdf_path}")
                raise HTTPException(status_code=403, detail="PDF file not accessible")

            logger.info(f"Successfully serving PDF: {pdf_path}")
            # Serve the file
            return FileResponse(
                path=str(pdf_path),
                media_type="application/pdf",
                filename=pdf_path.name,
                headers={
                    "Accept-Ranges": "bytes"
                },  # Enable partial content for PDF viewers
            )

        except HTTPException:
            # Re-raise HTTP exceptions as is
            raise
        except Exception as e:
            logger.error(f"Unexpected error serving PDF {path}: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to serve PDF file: {str(e)}"
            )

    # IMPORTANT: Specific routes must come BEFORE parameterized routes
    # to avoid route conflicts where 'search', 'folders', etc. are interpreted as document IDs

    @router.get("/api/documents", response_model=DocumentListResponse)
    async def list_documents(
        skip: int = Query(0, ge=0),
        limit: int = Query(50, ge=1, le=100),
        filters: Optional[Dict[str, Any]] = None,
        folder_name: Optional[str] = None,
    ):
        response = await db.list_documents(skip, limit, folder_name, filters)
        return response

    # Search endpoints - must come before {document_id} routes
    @router.get("/api/documents/search", response_model=SearchResponse)
    async def search_documents(
        query: str = Query(..., min_length=1),
        folder_name: Optional[str] = None,
        k: int = Query(4, ge=1, le=50),
        filters: Optional[Dict[str, Any]] = None,
    ):
        results = await db.search_documents(query, folder_name, k, filters)

        # Convert to SearchResult objects
        search_results = []
        for result in results:
            search_results.append(
                SearchResult(
                    id=result["id"],
                    title=result["title"],
                    authors=result["authors"],
                    journal_name=result.get("journal_name"),
                    publication_year=result.get("publication_year"),
                    folder_name=result.get("folder_name"),
                    keywords=result.get("keywords"),
                    similarity_score=result["similarity_score"],
                    snippet=result.get("snippet"),
                    url=result.get("url"),
                )
            )

        return SearchResponse(
            results=search_results,
            query=query,
            total_results=len(search_results),
        )

    @router.get("/api/documents/search/keywords", response_model=KeywordSearchResponse)
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

    # Folders endpoint - must come before {document_id} routes
    @router.get("/api/documents/folders", response_model=FoldersResponse)
    async def get_folders(base_path: Optional[str] = None):
        folders = await db.get_folders(base_path)
        return FoldersResponse(folders=folders)

    # Status endpoint - must come before {document_id} routes
    @router.get("/api/documents/status", response_model=StatusResponse)
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

    # NOW the parameterized routes come AFTER all specific routes
    @router.get("/api/documents/{document_id}", response_model=Document)
    async def get_document(document_id: UUID = FastAPIPath(...)):
        document = await db.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return document

    @router.get(
        "/api/documents/{document_id}/metadata", response_model=DocumentMetadata
    )
    async def get_document_metadata(document_id: UUID = FastAPIPath(...)):
        metadata = await db.get_document_metadata(document_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="Document not found")
        return metadata

    @router.get("/api/documents/{document_id}/summary", response_model=DocumentSummary)
    async def get_document_summary(document_id: UUID = FastAPIPath(...)):
        summary = await db.get_document_summary(document_id)
        if not summary:
            raise HTTPException(status_code=404, detail="Document not found")
        return summary

    @router.patch(
        "/api/documents/{document_id}/summary", response_model=DocumentSummary
    )
    async def update_document_summary(
        document_id: UUID = FastAPIPath(...),
        summary_data: UpdateSummaryRequest = Body(...),
    ):
        success = await db.update_document_summary(document_id, summary_data)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        return await db.get_document_summary(document_id)

    @router.post(
        "/documents/{document_id}/generate-summary", response_model=DocumentSummary
    )
    async def generate_document_summary(
        document_id: UUID = FastAPIPath(...),
    ):
        """Generate summary for a document using its markdown content"""
        try:
            # Get the document to access its markdown content
            document = await db.get_document(document_id)
            if not document:
                raise HTTPException(status_code=404, detail="Document not found")

            if not document.markdown:
                raise HTTPException(
                    status_code=400,
                    detail="Document has no markdown content to generate summary from",
                )

            # Import the summary generation function
            from .utils import generate_summary, get_genai_client

            # Generate summary using the document's markdown content
            genai_client = get_genai_client()
            summary_data = await generate_summary(document.markdown, genai_client)

            # Convert the summary data to UpdateSummaryRequest format
            from .models import UpdateSummaryRequest

            update_request = UpdateSummaryRequest(
                summary=summary_data.get("summary"),
                previous_work=summary_data.get("previous_work"),
                hypothesis=summary_data.get("hypothesis"),
                distinction=summary_data.get("distinction"),
                methodology=summary_data.get("methodology"),
                results=summary_data.get("results"),
                limitations=summary_data.get("limitations"),
                implications=summary_data.get("implication"),
            )

            # Update the document with the generated summary
            success = await db.update_document_summary(document_id, update_request)
            if not success:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to save generated summary to database",
                )

            # Return the updated summary
            return await db.get_document_summary(document_id)

        except HTTPException:
            # Re-raise HTTP exceptions as is
            raise
        except Exception as e:
            logger.error(f"Error generating summary for document {document_id}: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to generate summary: {str(e)}"
            )

    @router.patch(
        "/api/documents/{document_id}/metadata", response_model=DocumentMetadata
    )
    async def update_document_metadata(
        document_id: UUID = FastAPIPath(...),
        metadata_data: UpdateMetadataRequest = Body(...),
    ):
        success = await db.update_document_metadata(document_id, metadata_data)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        return await db.get_document_metadata(document_id)

    @router.patch("/api/documents/{document_id}/rating")
    async def update_document_rating(
        document_id: UUID = FastAPIPath(...),
        rating_data: UpdateRatingRequest = Body(...),
    ):
        """Update the rating for a document"""
        from .models import UpdateRatingRequest

        success = await db.update_document_rating(document_id, rating_data)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")

        # Return the updated document metadata with the new rating
        updated_metadata = await db.get_document_metadata(document_id)
        if not updated_metadata:
            raise HTTPException(status_code=404, detail="Document not found")

        return {
            "rating": updated_metadata.rating,
            "message": "Rating updated successfully",
        }

    @router.get(
        "/documents/{document_id}/similar", response_model=SimilarDocumentsResponse
    )
    async def find_similar_documents(
        document_id: UUID = FastAPIPath(...),
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

    # Chat endpoint
    @router.post("/api/documents/{document_id}/chat", response_model=ChatResponse)
    async def chat_with_document(
        document_id: UUID = FastAPIPath(...),
        chat_request: ChatRequest = Body(...),
    ):
        """Chat with a document using its content"""
        # Get the document first
        document = await db.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Generate chat response
        try:
            response_text = await db.chat_with_document(document, chat_request.message)

            # Create chat message for response
            from datetime import datetime
            import uuid

            chat_message = ChatMessage(
                id=str(uuid.uuid4()),
                role="assistant",
                content=response_text,
                timestamp=datetime.now().isoformat(),
            )

            return ChatResponse(message=chat_message, answer=response_text)
        except Exception as e:
            logger.error(f"Chat error for document {document_id}: {e}")
            raise HTTPException(
                status_code=500, detail="Failed to generate chat response"
            )

    @router.get("/api/documents/{document_id}/thumbnail")
    async def get_document_thumbnail(
        document_id: UUID = FastAPIPath(...),
        width: int = Query(300, ge=100, le=800, description="Thumbnail width"),
        height: int = Query(200, ge=100, le=600, description="Thumbnail height"),
    ):
        """Generate and serve a thumbnail image from the first page of the document's PDF"""
        try:
            # Get the document to find the PDF path
            document = await db.get_document(document_id)
            if not document:
                raise HTTPException(status_code=404, detail="Document not found")

            if not document.url:
                raise HTTPException(status_code=404, detail="Document has no PDF file")

            # Construct the PDF path
            # Assuming document.url contains the relative path from the docs directory
            base_directory = Path(os.getenv("DOCS_BASE_DIR", "docs")).resolve()
            pdf_path = (base_directory / document.url).resolve()

            # Security check: ensure the resolved path is still within base directory
            try:
                pdf_path.relative_to(base_directory)
            except ValueError:
                logger.error(
                    f"Security violation: PDF path outside base directory: {pdf_path}"
                )
                raise HTTPException(status_code=403, detail="Access denied")

            # Check if PDF file exists
            if not pdf_path.exists():
                logger.error(f"PDF file not found: {pdf_path}")
                raise HTTPException(status_code=404, detail="PDF file not found")

            if not pdf_path.is_file():
                raise HTTPException(status_code=400, detail="Path is not a file")

            if pdf_path.suffix.lower() != ".pdf":
                raise HTTPException(status_code=400, detail="File is not a PDF")

            # Generate thumbnail
            from .utils import generate_pdf_thumbnail

            thumbnail_buffer = generate_pdf_thumbnail(pdf_path, width, height)

            # Return the thumbnail as a streaming response
            return StreamingResponse(
                io.BytesIO(thumbnail_buffer.getvalue()),
                media_type="image/jpeg",
                headers={
                    "Cache-Control": "public, max-age=3600",  # Cache for 1 hour
                    "Content-Disposition": f"inline; filename=thumbnail_{document_id}.jpg",
                },
            )

        except HTTPException:
            # Re-raise HTTP exceptions as is
            raise
        except Exception as e:
            logger.error(f"Error generating thumbnail for document {document_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to generate thumbnail")

    return router
