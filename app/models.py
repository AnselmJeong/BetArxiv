from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class PaperBase(BaseModel):
    title: str
    authors: List[str]
    journal_name: Optional[str] = None
    volume_issue: Optional[str] = None
    publication_year: Optional[int] = None
    abstract: Optional[str] = None
    keywords: Optional[List[str]] = None


class PaperCreate(PaperBase):
    markdown: Optional[str] = None
    summary: Optional[str] = None
    distinction: Optional[str] = None
    methodology: Optional[str] = None
    results: Optional[str] = None
    implications: Optional[str] = None
    title_embedding: Optional[List[float]] = None
    abstract_embedding: Optional[List[float]] = None
    status: Optional[str] = "pending"


class Paper(PaperCreate):
    id: UUID


class PaperListItem(BaseModel):
    id: UUID
    title: str
    authors: List[str]
    journal_name: Optional[str]
    publication_year: Optional[int]
    abstract: Optional[str]


class PaperListResponse(BaseModel):
    papers: List[PaperListItem]
    pagination: dict


class SimilarPaper(BaseModel):
    id: UUID
    title: str
    authors: List[str]
    similarity_score: float


class SimilarPapersResponse(BaseModel):
    similar_papers: List[SimilarPaper]


class StatusResponse(BaseModel):
    total_papers: int
    processed: int
    pending: int
    errors: int
