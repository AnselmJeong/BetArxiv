import logging
from typing import List, Optional, Any, Dict
from uuid import UUID
from datetime import datetime
import os
from pathlib import Path
import json

import psycopg
from psycopg.rows import dict_row

from .models import (
    DocumentCreate,
    Document,
    DocumentListItem,
    DocumentMetadata,
    DocumentSummary,
    DocumentEmbedding,
    SearchResult,
    FolderInfo,
    UpdateSummaryRequest,
    UpdateMetadataRequest,
    DocumentListResponse,
    SearchResponse,
)

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, dsn: str):
        self.dsn = dsn
        self.pool: Optional[psycopg.AsyncConnection] = None

    async def connect(self):
        self.pool = await psycopg.AsyncConnection.connect(self.dsn, autocommit=True, row_factory=dict_row)
        logger.info("Connected to PostgreSQL.")

    async def close(self):
        if self.pool:
            await self.pool.close()
            logger.info("Closed PostgreSQL connection.")

    # Document operations
    async def insert_document(self, document: DocumentCreate) -> UUID:
        """Insert a new document into the database."""
        query = """
            INSERT INTO documents (
                title, authors, journal_name, publication_year, abstract,
                keywords, volume, issue, url, markdown, summary,
                distinction, methodology, results, implications,
                title_embedding, abstract_embedding, status, folder_name
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) RETURNING id
        """
        async with self.pool.cursor() as cur:
            await cur.execute(
                query,
                (
                    document.title,
                    document.authors,
                    document.journal_name,
                    document.publication_year,
                    document.abstract,
                    document.keywords,
                    document.volume,
                    document.issue,
                    document.url,
                    document.markdown,
                    document.summary,
                    document.distinction,
                    document.methodology,
                    document.results,
                    document.implications,
                    document.title_embedding,
                    document.abstract_embedding,
                    document.status,
                    document.folder_name,
                ),
            )
            row = await cur.fetchone()
            return row["id"]

    async def get_document(self, document_id: UUID) -> Optional[Document]:
        """Get a document by ID."""
        query = """
            SELECT id, title, authors, journal_name, publication_year,
                   abstract, keywords, volume, issue, url, markdown,
                   summary, distinction, methodology, results, implications,
                   title_embedding, abstract_embedding, status, folder_name
            FROM documents
            WHERE id = %s
        """
        async with self.pool.cursor() as cur:
            await cur.execute(query, (str(document_id),))
            row = await cur.fetchone()
            if row:
                row_dict = dict(row)
                # Parse embeddings from JSON strings if they exist
                if row_dict.get("title_embedding"):
                    row_dict["title_embedding"] = (
                        json.loads(row_dict["title_embedding"])
                        if isinstance(row_dict["title_embedding"], str)
                        else row_dict["title_embedding"]
                    )
                if row_dict.get("abstract_embedding"):
                    row_dict["abstract_embedding"] = (
                        json.loads(row_dict["abstract_embedding"])
                        if isinstance(row_dict["abstract_embedding"], str)
                        else row_dict["abstract_embedding"]
                    )
                return Document(**row_dict)
            return None

    async def get_document_metadata(self, document_id: UUID) -> Optional[DocumentMetadata]:
        """Get document metadata by ID."""
        query = """
            SELECT title, authors, journal_name, publication_year,
                   abstract, keywords, volume, issue, url, markdown
            FROM documents
            WHERE id = %s
        """
        async with self.pool.cursor() as cur:
            await cur.execute(query, (str(document_id),))
            row = await cur.fetchone()
            if row:
                return DocumentMetadata(**dict(row))
            return None

    async def get_document_summary(self, document_id: UUID) -> Optional[DocumentSummary]:
        query = """
        SELECT summary, distinction, methodology, results, implications 
        FROM documents WHERE id=%s
        """
        async with self.pool.cursor() as cur:
            await cur.execute(query, (str(document_id),))
            row = await cur.fetchone()
            if row:
                return DocumentSummary(**row)
            return None

    async def get_document_embedding(self, document_id: UUID) -> Optional[DocumentEmbedding]:
        query = "SELECT title_embedding, abstract_embedding FROM documents WHERE id=%s"
        async with self.pool.cursor() as cur:
            await cur.execute(query, (str(document_id),))
            row = await cur.fetchone()
            if row:
                row_dict = dict(row)
                # Parse embeddings from JSON strings if they exist
                if row_dict.get("title_embedding"):
                    row_dict["title_embedding"] = (
                        json.loads(row_dict["title_embedding"])
                        if isinstance(row_dict["title_embedding"], str)
                        else row_dict["title_embedding"]
                    )
                if row_dict.get("abstract_embedding"):
                    row_dict["abstract_embedding"] = (
                        json.loads(row_dict["abstract_embedding"])
                        if isinstance(row_dict["abstract_embedding"], str)
                        else row_dict["abstract_embedding"]
                    )
                return DocumentEmbedding(**row_dict)
            return None

    async def update_document_summary(self, document_id: UUID, summary_data: UpdateSummaryRequest) -> bool:
        fields = []
        values = []
        for field, value in summary_data.model_dump(exclude_unset=True).items():
            if value is not None:
                fields.append(f"{field}=%s")
                values.append(value)

        if not fields:
            return False

        query = f"UPDATE documents SET {', '.join(fields)}, updated_at=NOW() WHERE id=%s"
        values.append(str(document_id))

        async with self.pool.cursor() as cur:
            await cur.execute(query, values)
            return cur.rowcount > 0

    async def update_document_metadata(self, document_id: UUID, metadata_data: UpdateMetadataRequest) -> bool:
        data = metadata_data.model_dump(exclude_unset=True)
        fields = []
        values = []

        for field, value in data.items():
            if value is not None:
                fields.append(f"{field}=%s")
                values.append(value)

        if not fields:
            return False

        query = f"UPDATE documents SET {', '.join(fields)}, updated_at=NOW() WHERE id=%s"
        values.append(str(document_id))

        async with self.pool.cursor() as cur:
            await cur.execute(query, values)
            return cur.rowcount > 0

    async def list_documents(
        self,
        skip: int = 0,
        limit: int = 50,
        folder_name: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> DocumentListResponse:
        """List documents with optional filtering."""
        where_conditions = []
        params = []

        if folder_name:
            where_conditions.append("folder_name = %s")
            params.append(folder_name)

        if filters:
            for key, value in filters.items():
                if key in ["title", "authors", "journal_name", "publication_year", "keywords"]:
                    where_conditions.append(f"{key} = %s")
                    params.append(value)

        where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""

        count_query = f"SELECT COUNT(*) FROM documents {where_clause}"
        query = f"""
            SELECT id, title, authors, journal_name, publication_year,
                   abstract, folder_name
            FROM documents
            {where_clause}
            ORDER BY publication_year DESC, title
            LIMIT %s OFFSET %s
        """

        async with self.pool.cursor() as cur:
            await cur.execute(count_query, params)
            total_row = await cur.fetchone()
            total = total_row["count"]

            await cur.execute(query, params + [limit, skip])
            rows = await cur.fetchall()
            documents = [DocumentListItem(**dict(row)) for row in rows]

            return DocumentListResponse(documents=documents, total=total, skip=skip, limit=limit)

    async def search_documents(
        self, query: str, folder_name: Optional[str] = None, k: int = 4, filters: Optional[Dict[str, Any]] = None
    ) -> SearchResponse:
        """Search documents using text similarity."""
        where_conditions = []
        params = [query]

        if folder_name:
            where_conditions.append("folder_name = %s")
            params.append(folder_name)

        if filters:
            for key, value in filters.items():
                if key in ["title", "authors", "journal_name", "publication_year", "keywords"]:
                    where_conditions.append(f"{key} = %s")
                    params.append(value)

        where_clause = f"AND {' AND '.join(where_conditions)}" if where_conditions else ""

        search_query = f"""
            SELECT id, title, authors,
                   (
                       CASE WHEN title ILIKE %s THEN 0.8 ELSE 0 END +
                       CASE WHEN abstract ILIKE %s THEN 0.5 ELSE 0 END +
                       CASE WHEN EXISTS (SELECT 1 FROM unnest(authors) a WHERE a ILIKE %s) THEN 0.3 ELSE 0 END
                   ) as similarity_score
            FROM documents
            WHERE (title ILIKE %s OR abstract ILIKE %s OR EXISTS (SELECT 1 FROM unnest(authors) a WHERE a ILIKE %s))
            {where_clause}
            ORDER BY similarity_score DESC
            LIMIT %s
        """

        search_term = f"%{query}%"
        search_params = (
            [search_term, search_term, search_term, search_term, search_term, search_term] + params[1:] + [k]
        )

        async with self.pool.cursor() as cur:
            await cur.execute(search_query, search_params)
            rows = await cur.fetchall()

            results = [
                SearchResult(
                    id=row["id"], title=row["title"], authors=row["authors"], similarity_score=row["similarity_score"]
                )
                for row in rows
            ]

            return SearchResponse(results=results, query=query, total_results=len(results))

    async def get_folders(self, base_path: Optional[str] = None) -> List[FolderInfo]:
        query = "SELECT DISTINCT folder_name FROM documents WHERE folder_name IS NOT NULL"
        async with self.pool.cursor() as cur:
            await cur.execute(query)
            rows = await cur.fetchall()
            folders = []
            for row in rows:
                folder_name = row["folder_name"]
                if base_path:
                    folder_path = os.path.join(base_path, folder_name)
                else:
                    folder_path = folder_name
                folders.append(FolderInfo(name=folder_name, path=folder_path))
            return folders

    async def get_status(self, document_id: Optional[UUID] = None):
        if document_id:
            query = "SELECT status FROM documents WHERE id=%s"
            async with self.pool.cursor() as cur:
                await cur.execute(query, (str(document_id),))
                row = await cur.fetchone()
                return row["status"] if row else None
        else:
            query = "SELECT status, COUNT(*) as count FROM documents GROUP BY status"
            async with self.pool.cursor() as cur:
                await cur.execute(query)
                return await cur.fetchall()

    async def find_similar_documents(
        self,
        document_id: UUID,
        limit: int = 10,
        threshold: float = 0.7,
        title_weight: float = 0.75,
        abstract_weight: float = 0.25,
        include_snippet: bool = True,
        folder_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        # Get the reference document's embeddings
        ref_doc = await self.get_document_embedding(document_id)
        if not ref_doc or not ref_doc.title_embedding or not ref_doc.abstract_embedding:
            return []

        return await self.find_similar_documents_by_embeddings(
            ref_doc.title_embedding,
            ref_doc.abstract_embedding,
            limit=limit,
            threshold=threshold,
            title_weight=title_weight,
            abstract_weight=abstract_weight,
            include_snippet=include_snippet,
            folder_name=folder_name,
            exclude_document_id=document_id,
        )

    async def find_similar_documents_by_embeddings(
        self,
        title_embedding: List[float],
        abstract_embedding: List[float],
        limit: int = 10,
        threshold: float = 0.7,
        title_weight: float = 0.75,
        abstract_weight: float = 0.25,
        include_snippet: bool = True,
        folder_name: Optional[str] = None,
        exclude_document_id: Optional[UUID] = None,
    ) -> List[Dict[str, Any]]:
        where_conditions = ["title_embedding IS NOT NULL AND abstract_embedding IS NOT NULL"]
        where_params = []

        if folder_name:
            where_conditions.append("folder_name = %s")
            where_params.append(folder_name)

        if exclude_document_id:
            where_conditions.append("id != %s")
            where_params.append(str(exclude_document_id))

        where_clause = f"WHERE {' AND '.join(where_conditions)}"

        query = f"""
            WITH similarity_scores AS (
                SELECT 
                    id,
                    title,
                    abstract,
                    authors,
                    journal_name,
                    publication_year,
                    folder_name,
                    (
                        {title_weight} * (1 - (title_embedding <=> %s::vector)) +
                        {abstract_weight} * (1 - (abstract_embedding <=> %s::vector))
                    ) as similarity
                FROM documents
                {where_clause}
            )
            SELECT *
            FROM similarity_scores
            WHERE similarity >= %s
            ORDER BY similarity DESC
            LIMIT %s
        """

        # Proper parameter order: embeddings first, then threshold, limit, then where clause params
        params = [title_embedding, abstract_embedding] + where_params + [threshold, limit]

        async with self.pool.cursor() as cur:
            await cur.execute(query, params)
            rows = await cur.fetchall()
            return [dict(row) for row in rows]

    async def search_by_keywords(
        self,
        keywords: List[str],
        search_mode: str = "any",  # "any" (OR) or "all" (AND)
        exact_match: bool = False,
        case_sensitive: bool = False,
        folder_name: Optional[str] = None,
        limit: int = 50,
        include_snippet: bool = True,
    ) -> List[Dict[str, Any]]:
        where_conditions = []
        params = []

        # Build keyword search conditions
        keyword_conditions = []
        for keyword in keywords:
            if exact_match:
                if case_sensitive:
                    keyword_conditions.append("EXISTS (SELECT 1 FROM unnest(keywords) k WHERE k = %s)")
                else:
                    keyword_conditions.append("EXISTS (SELECT 1 FROM unnest(keywords) k WHERE LOWER(k) = LOWER(%s))")
            else:
                if case_sensitive:
                    keyword_conditions.append("EXISTS (SELECT 1 FROM unnest(keywords) k WHERE k LIKE %s)")
                else:
                    keyword_conditions.append("EXISTS (SELECT 1 FROM unnest(keywords) k WHERE LOWER(k) LIKE LOWER(%s))")
            params.append(f"%{keyword}%" if not exact_match else keyword)

        if search_mode == "all":
            where_conditions.append(f"({' AND '.join(keyword_conditions)})")
        else:  # "any"
            where_conditions.append(f"({' OR '.join(keyword_conditions)})")

        if folder_name:
            where_conditions.append("folder_name = %s")
            params.append(folder_name)

        where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""

        query = f"""
            SELECT 
                id, title, authors, journal_name, publication_year,
                abstract, keywords, folder_name
            FROM documents
            {where_clause}
            ORDER BY created_at DESC
            LIMIT %s
        """
        params.append(limit)

        async with self.pool.cursor() as cur:
            await cur.execute(query, params)
            rows = await cur.fetchall()
            return [dict(row) for row in rows]

    async def search_combined(
        self,
        text_query: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        keyword_mode: str = "any",
        exact_keyword_match: bool = False,
        folder_name: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 20,
        include_snippet: bool = True,
    ) -> List[Dict[str, Any]]:
        where_conditions = []
        params = []

        # Text search condition
        if text_query:
            where_conditions.append(
                "(LOWER(title) LIKE %s OR LOWER(abstract) LIKE %s OR EXISTS (SELECT 1 FROM unnest(authors) a WHERE LOWER(a) LIKE %s))"
            )
            search_term = f"%{text_query.lower()}%"
            params.extend([search_term, search_term, search_term])

        # Keyword search conditions
        if keywords:
            keyword_conditions = []
            for keyword in keywords:
                if exact_keyword_match:
                    keyword_conditions.append("EXISTS (SELECT 1 FROM unnest(keywords) k WHERE LOWER(k) = LOWER(%s))")
                else:
                    keyword_conditions.append("EXISTS (SELECT 1 FROM unnest(keywords) k WHERE LOWER(k) LIKE LOWER(%s))")
                params.append(f"%{keyword}%" if not exact_keyword_match else keyword)

            if keyword_mode == "all":
                where_conditions.append(f"({' AND '.join(keyword_conditions)})")
            else:  # "any"
                where_conditions.append(f"({' OR '.join(keyword_conditions)})")

        # Additional filters
        if filters:
            for key, value in filters.items():
                if key == "publication_year":
                    where_conditions.append("publication_year = %s")
                    params.append(value)
                elif key == "journal_name":
                    where_conditions.append("journal_name = %s")
                    params.append(value)
                elif key == "status":
                    where_conditions.append("status = %s")
                    params.append(value)

        if folder_name:
            where_conditions.append("folder_name = %s")
            params.append(folder_name)

        where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""

        query = f"""
            SELECT 
                id, title, authors, journal_name, publication_year,
                abstract, keywords, folder_name
            FROM documents
            {where_clause}
            ORDER BY created_at DESC
            LIMIT %s
        """
        params.append(limit)

        async with self.pool.cursor() as cur:
            await cur.execute(query, params)
            rows = await cur.fetchall()
            return [dict(row) for row in rows]

    async def get_all_keywords(self, folder_name: Optional[str] = None) -> List[Dict[str, Any]]:
        where_clause = "WHERE folder_name = %s" if folder_name else ""
        query = f"""
            SELECT DISTINCT unnest(keywords) as keyword, COUNT(*) as count
            FROM documents
            {where_clause}
            GROUP BY keyword
            ORDER BY count DESC
        """
        params = [folder_name] if folder_name else []

        async with self.pool.cursor() as cur:
            await cur.execute(query, params)
            rows = await cur.fetchall()
            return [dict(row) for row in rows]

    async def update_paper_status(self, document_id: UUID, status: str) -> bool:
        """Update the status of a document/paper"""
        query = "UPDATE documents SET status = %s, updated_at = NOW() WHERE id = %s"
        async with self.pool.cursor() as cur:
            await cur.execute(query, (status, str(document_id)))
            return cur.rowcount > 0
