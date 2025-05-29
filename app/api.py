import logging
from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException,
    BackgroundTasks,
    Query,
    Body,
)
from fastapi.responses import JSONResponse
from typing import Optional
from uuid import UUID
import shutil
import tempfile
import os

from .models import Paper, PaperListResponse, SimilarPapersResponse, StatusResponse
from .db import Database
from .paper_processor import process_pdf
from ollama import AsyncClient as OllamaAsyncClient

logger = logging.getLogger(__name__)


def get_router(db: Database, ollama_client: OllamaAsyncClient, pdf_queue):
    router = APIRouter()

    @router.post("/papers/upload", response_model=Paper)
    async def upload_paper(file: UploadFile = File(...)):
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
        papers, total = await db.list_papers(page, per_page, search, year)
        return PaperListResponse(
            papers=papers,
            pagination={"page": page, "per_page": per_page, "total": total},
        )

    @router.get("/papers/{id}", response_model=Paper)
    async def get_paper(id: UUID):
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
        results = await db.get_similar_papers(id, limit, threshold)
        return SimilarPapersResponse(similar_papers=results)

    @router.post("/papers/process-directory")
    async def process_directory(
        background_tasks: BackgroundTasks, directory: Optional[str] = Body(None)
    ):
        # Enqueue all PDFs in the directory for processing
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
        status = await db.get_status(paper_id)
        if not status:
            raise HTTPException(status_code=404, detail="Not found.")
        return status

    return router
