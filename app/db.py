import logging
from typing import List, Optional, Any, Dict
from uuid import UUID
from datetime import datetime
import os
from pathlib import Path

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
)

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, dsn: str):
        self.dsn = dsn
        self.pool: Optional[psycopg.AsyncConnection] = None

    async def connect(self):
        self.pool = await psycopg.AsyncConnection.connect(
            self.dsn, autocommit=True, row_factory=dict_row
        )
        logger.info("Connected to PostgreSQL.")

    async def close(self):
        if self.pool:
            await self.pool.close()
            logger.info("Closed PostgreSQL connection.")

    # Document operations
    async def insert_document(self, document: DocumentCreate) -> UUID:
        query = """
        INSERT INTO papers (
            title, authors, journal_name, volume_issue, publication_year, abstract, keywords,
            markdown, summary, distinction, methodology, results, implications,
            title_embedding, abstract_embedding, status, folder_name, url
        ) VALUES (
            %(title)s, %(authors)s, %(journal_name)s, %(volume_issue)s, %(year_of_publication)s, %(abstract)s, %(keywords)s,
            %(markdown)s, %(summary)s, %(distinction)s, %(methodology)s, %(results)s, %(implications)s,
            %(title_embedding)s, %(abstract_embedding)s, %(status)s, %(folder_name)s, %(url)s
        ) RETURNING id;
        """
        # Map new field names to database column names
        document_data = document.model_dump()
        document_data["volume_issue"] = (
            f"{document.volume or ''} {document.issue or ''}".strip() or None
        )
        document_data["publication_year"] = document.year_of_publication

        async with self.pool.cursor() as cur:
            await cur.execute(query, document_data)
            row = await cur.fetchone()
            return row["id"]

    async def get_document(self, document_id: UUID) -> Optional[Document]:
        query = "SELECT * FROM papers WHERE id=%s"
        async with self.pool.cursor() as cur:
            await cur.execute(query, (str(document_id),))
            row = await cur.fetchone()
            if row:
                # Map database fields to new model fields
                row_data = dict(row)
                if row_data.get("publication_year"):
                    row_data["year_of_publication"] = row_data["publication_year"]
                if row_data.get("volume_issue"):
                    parts = row_data["volume_issue"].split(" ", 1)
                    row_data["volume"] = parts[0] if parts else None
                    row_data["issue"] = parts[1] if len(parts) > 1 else None
                return Document(**row_data)
            return None

    async def get_document_metadata(
        self, document_id: UUID
    ) -> Optional[DocumentMetadata]:
        query = """
        SELECT title, authors, journal_name, publication_year, abstract, keywords, 
               volume_issue, url, markdown 
        FROM papers WHERE id=%s
        """
        async with self.pool.cursor() as cur:
            await cur.execute(query, (str(document_id),))
            row = await cur.fetchone()
            if row:
                row_data = dict(row)
                row_data["year_of_publication"] = row_data.pop("publication_year", None)
                if row_data.get("volume_issue"):
                    parts = row_data["volume_issue"].split(" ", 1)
                    row_data["volume"] = parts[0] if parts else None
                    row_data["issue"] = parts[1] if len(parts) > 1 else None
                row_data.pop("volume_issue", None)
                return DocumentMetadata(**row_data)
            return None

    async def get_document_summary(
        self, document_id: UUID
    ) -> Optional[DocumentSummary]:
        query = """
        SELECT summary, distinction, methodology, results, implications 
        FROM papers WHERE id=%s
        """
        async with self.pool.cursor() as cur:
            await cur.execute(query, (str(document_id),))
            row = await cur.fetchone()
            if row:
                return DocumentSummary(**row)
            return None

    async def get_document_embedding(
        self, document_id: UUID
    ) -> Optional[DocumentEmbedding]:
        query = "SELECT title_embedding, abstract_embedding FROM papers WHERE id=%s"
        async with self.pool.cursor() as cur:
            await cur.execute(query, (str(document_id),))
            row = await cur.fetchone()
            if row:
                return DocumentEmbedding(**row)
            return None

    async def update_document_summary(
        self, document_id: UUID, summary_data: UpdateSummaryRequest
    ) -> bool:
        fields = []
        values = []
        for field, value in summary_data.model_dump(exclude_unset=True).items():
            if value is not None:
                fields.append(f"{field}=%s")
                values.append(value)

        if not fields:
            return False

        query = f"UPDATE papers SET {', '.join(fields)}, updated_at=NOW() WHERE id=%s"
        values.append(str(document_id))

        async with self.pool.cursor() as cur:
            await cur.execute(query, values)
            return cur.rowcount > 0

    async def update_document_metadata(
        self, document_id: UUID, metadata_data: UpdateMetadataRequest
    ) -> bool:
        data = metadata_data.model_dump(exclude_unset=True)
        fields = []
        values = []

        for field, value in data.items():
            if value is not None:
                if field == "year_of_publication":
                    fields.append("publication_year=%s")
                    values.append(value)
                elif field in ["volume", "issue"]:
                    # Handle volume/issue special case - we'll need to read current value first
                    continue
                else:
                    fields.append(f"{field}=%s")
                    values.append(value)

        # Handle volume/issue update
        if "volume" in data or "issue" in data:
            current_doc = await self.get_document(document_id)
            if current_doc:
                new_volume = data.get("volume", current_doc.volume or "")
                new_issue = data.get("issue", current_doc.issue or "")
                volume_issue = f"{new_volume} {new_issue}".strip() or None
                fields.append("volume_issue=%s")
                values.append(volume_issue)

        if not fields:
            return False

        query = f"UPDATE papers SET {', '.join(fields)}, updated_at=NOW() WHERE id=%s"
        values.append(str(document_id))

        async with self.pool.cursor() as cur:
            await cur.execute(query, values)
            return cur.rowcount > 0

    async def list_documents(
        self,
        skip: int = 0,
        limit: int = 50,
        filters: Optional[Dict[str, Any]] = None,
        folder_name: Optional[str] = None,
    ) -> tuple[List[DocumentListItem], int]:
        where_conditions = []
        params: List[Any] = []

        if folder_name:
            where_conditions.append("folder_name = %s")
            params.append(folder_name)

        if filters:
            for key, value in filters.items():
                if key == "year_of_publication":
                    where_conditions.append("publication_year = %s")
                    params.append(value)
                elif key == "search":
                    where_conditions.append(
                        "(LOWER(title) LIKE %s OR %s = ANY(LOWER(authors)) OR %s = ANY(LOWER(keywords)))"
                    )
                    search_term = f"%{value.lower()}%"
                    params.extend([search_term, value.lower(), value.lower()])
                elif key in ["journal_name", "status"]:
                    where_conditions.append(f"{key} = %s")
                    params.append(value)

        where_clause = (
            f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""
        )

        count_query = f"SELECT COUNT(*) FROM papers {where_clause}"
        query = f"""
            SELECT id, title, authors, journal_name, publication_year as year_of_publication, 
                   abstract, folder_name
            FROM papers {where_clause}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """

        params_count = params.copy()
        params.extend([limit, skip])

        async with self.pool.cursor() as cur:
            await cur.execute(count_query, params_count)
            total = (await cur.fetchone())["count"]
            await cur.execute(query, params)
            rows = await cur.fetchall()
            documents = [DocumentListItem(**row) for row in rows]
            return documents, total

    async def search_documents(
        self,
        query: str,
        folder_name: Optional[str] = None,
        k: int = 4,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        # For now, implement a simple text-based search
        # TODO: Implement semantic search using embeddings
        where_conditions = [
            "(LOWER(title) LIKE %s OR LOWER(abstract) LIKE %s OR %s = ANY(LOWER(authors)) OR %s = ANY(LOWER(keywords)))"
        ]
        search_term = f"%{query.lower()}%"
        params = [search_term, search_term, query.lower(), query.lower()]

        if folder_name:
            where_conditions.append("folder_name = %s")
            params.append(folder_name)

        if filters:
            for key, value in filters.items():
                if key == "year_of_publication":
                    where_conditions.append("publication_year = %s")
                    params.append(value)
                elif key in ["journal_name", "status"]:
                    where_conditions.append(f"{key} = %s")
                    params.append(value)

        where_clause = f"WHERE {' AND '.join(where_conditions)}"
        search_query = f"""
            SELECT id, title, authors, abstract,
                   1.0 as similarity_score,
                   SUBSTRING(abstract, 1, 200) as snippet
            FROM papers {where_clause}
            ORDER BY created_at DESC
            LIMIT %s
        """
        params.append(k)

        async with self.pool.cursor() as cur:
            await cur.execute(search_query, params)
            rows = await cur.fetchall()
            return [
                SearchResult(
                    id=row["id"],
                    title=row["title"],
                    authors=row["authors"],
                    similarity_score=row["similarity_score"],
                    snippet=row["snippet"],
                )
                for row in rows
            ]

    async def get_folders(self, base_path: Optional[str] = None) -> List[FolderInfo]:
        # Get distinct folder names from database
        query = """
        SELECT folder_name, COUNT(*) as document_count 
        FROM papers 
        WHERE folder_name IS NOT NULL 
        GROUP BY folder_name
        ORDER BY folder_name
        """

        async with self.pool.cursor() as cur:
            await cur.execute(query)
            rows = await cur.fetchall()

            folders = []
            for row in rows:
                folder_name = row["folder_name"]
                folders.append(
                    FolderInfo(
                        name=folder_name,
                        path=folder_name,  # Assuming folder_name contains the path
                        document_count=row["document_count"],
                        subfolders=[],  # TODO: Implement subfolder detection
                    )
                )

            return folders

    # Legacy methods for backward compatibility
    async def insert_paper(self, paper: DocumentCreate) -> UUID:
        return await self.insert_document(paper)

    async def update_paper_status(self, paper_id: UUID, status: str):
        query = "UPDATE papers SET status=%s, updated_at=NOW() WHERE id=%s"
        async with self.pool.cursor() as cur:
            await cur.execute(query, (status, str(paper_id)))

    async def get_paper(self, paper_id: UUID) -> Optional[Document]:
        return await self.get_document(paper_id)

    async def list_papers(
        self, page: int, per_page: int, search: Optional[str], year: Optional[int]
    ) -> tuple[List[DocumentListItem], int]:
        skip = (page - 1) * per_page
        filters = {}
        if search:
            filters["search"] = search
        if year:
            filters["year_of_publication"] = year

        documents, total = await self.list_documents(
            skip=skip, limit=per_page, filters=filters
        )
        return documents, total

    async def get_similar_papers(
        self, paper_id: UUID, limit: int, threshold: float
    ) -> List[dict]:
        # Get the reference embeddings
        query = "SELECT title_embedding, abstract_embedding FROM papers WHERE id=%s"
        async with self.pool.cursor() as cur:
            await cur.execute(query, (str(paper_id),))
            row = await cur.fetchone()
            if not row:
                return []
            title_emb, abstract_emb = row["title_embedding"], row["abstract_embedding"]
            # Find similar papers using cosine similarity (pgvector)
            sim_query = """
            SELECT id, title, authors,
                (1 - (title_embedding <=> %s) + 1 - (abstract_embedding <=> %s))/2 AS similarity_score
            FROM papers
            WHERE id != %s
            ORDER BY similarity_score DESC
            LIMIT %s
            """
            await cur.execute(
                sim_query, (title_emb, abstract_emb, str(paper_id), limit)
            )
            results = await cur.fetchall()
            return [
                {
                    "id": r["id"],
                    "title": r["title"],
                    "authors": r["authors"],
                    "similarity_score": float(r["similarity_score"]),
                }
                for r in results
                if r["similarity_score"] >= threshold
            ]

    async def get_status(self, paper_id: Optional[UUID] = None):
        async with self.pool.cursor() as cur:
            if paper_id:
                await cur.execute(
                    "SELECT status FROM papers WHERE id=%s", (str(paper_id),)
                )
                row = await cur.fetchone()
                if row:
                    return {"status": row["status"]}
                return None
            else:
                await cur.execute("SELECT COUNT(*) FROM papers")
                total = (await cur.fetchone())["count"]
                await cur.execute(
                    "SELECT COUNT(*) FROM papers WHERE status='processed'"
                )
                processed = (await cur.fetchone())["count"]
                await cur.execute("SELECT COUNT(*) FROM papers WHERE status='pending'")
                pending = (await cur.fetchone())["count"]
                await cur.execute("SELECT COUNT(*) FROM papers WHERE status='error'")
                errors = (await cur.fetchone())["count"]
                return {
                    "total_documents": total,
                    "processed": processed,
                    "pending": pending,
                    "errors": errors,
                }

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
        """
        Find similar documents using weighted embedding similarity.

        Args:
            document_id: ID of the reference document
            limit: Maximum number of results to return
            threshold: Minimum similarity score threshold
            title_weight: Weight for title embedding similarity (default 0.75 for 3:1 ratio)
            abstract_weight: Weight for abstract embedding similarity (default 0.25)
            include_snippet: Whether to include abstract snippets
            folder_name: Optional folder to limit search scope

        Returns:
            List of similar documents with weighted similarity scores
        """
        # Normalize weights to ensure they sum to 1
        total_weight = title_weight + abstract_weight
        if total_weight > 0:
            title_weight = title_weight / total_weight
            abstract_weight = abstract_weight / total_weight
        else:
            title_weight, abstract_weight = 0.5, 0.5

        # Get the reference embeddings
        query = """
        SELECT title_embedding, abstract_embedding, title, abstract 
        FROM papers WHERE id=%s
        """
        async with self.pool.cursor() as cur:
            await cur.execute(query, (str(document_id),))
            row = await cur.fetchone()
            if not row:
                return []

            ref_title_emb = row["title_embedding"]
            ref_abstract_emb = row["abstract_embedding"]

            if not ref_title_emb or not ref_abstract_emb:
                return []

            # Build the similarity query with optional folder filtering
            where_conditions = [
                "id != %s",
                "title_embedding IS NOT NULL",
                "abstract_embedding IS NOT NULL",
            ]
            params = [str(document_id)]

            if folder_name:
                where_conditions.append("folder_name = %s")
                params.append(folder_name)

            where_clause = f"WHERE {' AND '.join(where_conditions)}"

            # Build the SELECT fields
            select_fields = [
                "id",
                "title",
                "authors",
                "folder_name",
                f"(1 - (title_embedding <=> %s)) AS title_similarity",
                f"(1 - (abstract_embedding <=> %s)) AS abstract_similarity",
                f"({title_weight} * (1 - (title_embedding <=> %s)) + {abstract_weight} * (1 - (abstract_embedding <=> %s))) AS similarity_score",
            ]

            if include_snippet:
                select_fields.append("SUBSTRING(abstract, 1, 200) as snippet")

            # Execute the similarity search
            sim_query = f"""
            SELECT {", ".join(select_fields)}
            FROM papers 
            {where_clause}
            HAVING similarity_score >= %s
            ORDER BY similarity_score DESC
            LIMIT %s
            """

            # Parameters: ref_title_emb (3x), ref_abstract_emb (3x), threshold, limit
            search_params = params + [
                ref_title_emb,  # for title_similarity
                ref_abstract_emb,  # for abstract_similarity
                ref_title_emb,  # for weighted similarity_score
                ref_abstract_emb,  # for weighted similarity_score
                threshold,  # for HAVING clause
                limit,  # for LIMIT
            ]

            await cur.execute(sim_query, search_params)
            results = await cur.fetchall()

            return [
                {
                    "id": r["id"],
                    "title": r["title"],
                    "authors": r["authors"],
                    "similarity_score": float(r["similarity_score"]),
                    "title_similarity": float(r["title_similarity"]),
                    "abstract_similarity": float(r["abstract_similarity"]),
                    "snippet": r.get("snippet") if include_snippet else None,
                    "folder_name": r["folder_name"],
                }
                for r in results
            ]

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
        """
        Find similar documents using provided embeddings (useful for search queries).

        Args:
            title_embedding: Title embedding vector
            abstract_embedding: Abstract embedding vector
            limit: Maximum number of results
            threshold: Minimum similarity threshold
            title_weight: Weight for title similarity (default 0.75 for 3:1 ratio)
            abstract_weight: Weight for abstract similarity (default 0.25)
            include_snippet: Whether to include snippets
            folder_name: Optional folder filter
            exclude_document_id: Optional document ID to exclude from results

        Returns:
            List of similar documents with weighted similarity scores
        """
        # Normalize weights
        total_weight = title_weight + abstract_weight
        if total_weight > 0:
            title_weight = title_weight / total_weight
            abstract_weight = abstract_weight / total_weight
        else:
            title_weight, abstract_weight = 0.5, 0.5

        # Build where conditions
        where_conditions = [
            "title_embedding IS NOT NULL",
            "abstract_embedding IS NOT NULL",
        ]
        params = []

        if folder_name:
            where_conditions.append("folder_name = %s")
            params.append(folder_name)

        if exclude_document_id:
            where_conditions.append("id != %s")
            params.append(str(exclude_document_id))

        where_clause = (
            f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""
        )

        # Build SELECT fields
        select_fields = [
            "id",
            "title",
            "authors",
            "folder_name",
            f"(1 - (title_embedding <=> %s)) AS title_similarity",
            f"(1 - (abstract_embedding <=> %s)) AS abstract_similarity",
            f"({title_weight} * (1 - (title_embedding <=> %s)) + {abstract_weight} * (1 - (abstract_embedding <=> %s))) AS similarity_score",
        ]

        if include_snippet:
            select_fields.append("SUBSTRING(abstract, 1, 200) as snippet")

        # Execute query
        search_query = f"""
        SELECT {", ".join(select_fields)}
        FROM papers 
        {where_clause}
        HAVING similarity_score >= %s
        ORDER BY similarity_score DESC
        LIMIT %s
        """

        # Parameters: where params + embeddings (4x) + threshold + limit
        search_params = params + [
            title_embedding,  # for title_similarity
            abstract_embedding,  # for abstract_similarity
            title_embedding,  # for weighted similarity_score
            abstract_embedding,  # for weighted similarity_score
            threshold,  # for HAVING clause
            limit,  # for LIMIT
        ]

        async with self.pool.cursor() as cur:
            await cur.execute(search_query, search_params)
            results = await cur.fetchall()

            return [
                {
                    "id": r["id"],
                    "title": r["title"],
                    "authors": r["authors"],
                    "similarity_score": float(r["similarity_score"]),
                    "title_similarity": float(r["title_similarity"]),
                    "abstract_similarity": float(r["abstract_similarity"]),
                    "snippet": r.get("snippet") if include_snippet else None,
                    "folder_name": r["folder_name"],
                }
                for r in results
            ]

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
        """
        Search documents by keywords with flexible matching options.

        Args:
            keywords: List of keywords to search for
            search_mode: "any" for OR logic, "all" for AND logic
            exact_match: Whether to use exact keyword matching
            case_sensitive: Whether search is case sensitive
            folder_name: Optional folder to limit search
            limit: Maximum number of results
            include_snippet: Whether to include abstract snippets

        Returns:
            List of documents matching the keyword criteria
        """
        if not keywords:
            return []

        # Prepare keywords for search
        if case_sensitive:
            search_keywords = keywords
        else:
            search_keywords = [kw.lower() for kw in keywords]

        # Build WHERE conditions
        where_conditions = ["keywords IS NOT NULL"]
        params = []

        if folder_name:
            where_conditions.append("folder_name = %s")
            params.append(folder_name)

        # Build keyword search condition
        if exact_match:
            if search_mode == "all":
                # All keywords must be present (exact match)
                keyword_conditions = []
                for keyword in search_keywords:
                    if case_sensitive:
                        keyword_conditions.append("%s = ANY(keywords)")
                    else:
                        keyword_conditions.append(
                            "%s = ANY(ARRAY(SELECT LOWER(unnest(keywords))))"
                        )
                    params.append(keyword)
                where_conditions.append(f"({' AND '.join(keyword_conditions)})")
            else:
                # Any keyword can be present (exact match)
                if case_sensitive:
                    where_conditions.append("keywords && %s")
                    params.append(search_keywords)
                else:
                    where_conditions.append(
                        "ARRAY(SELECT LOWER(unnest(keywords))) && %s"
                    )
                    params.append(search_keywords)
        else:
            # Fuzzy matching within keywords
            if search_mode == "all":
                # All keywords must match (fuzzy)
                keyword_conditions = []
                for keyword in search_keywords:
                    if case_sensitive:
                        keyword_conditions.append(
                            "EXISTS(SELECT 1 FROM unnest(keywords) AS kw WHERE kw LIKE %s)"
                        )
                        params.append(f"%{keyword}%")
                    else:
                        keyword_conditions.append(
                            "EXISTS(SELECT 1 FROM unnest(keywords) AS kw WHERE LOWER(kw) LIKE %s)"
                        )
                        params.append(f"%{keyword}%")
                where_conditions.append(f"({' AND '.join(keyword_conditions)})")
            else:
                # Any keyword can match (fuzzy)
                keyword_conditions = []
                for keyword in search_keywords:
                    if case_sensitive:
                        keyword_conditions.append(
                            "EXISTS(SELECT 1 FROM unnest(keywords) AS kw WHERE kw LIKE %s)"
                        )
                        params.append(f"%{keyword}%")
                    else:
                        keyword_conditions.append(
                            "EXISTS(SELECT 1 FROM unnest(keywords) AS kw WHERE LOWER(kw) LIKE %s)"
                        )
                        params.append(f"%{keyword}%")
                where_conditions.append(f"({' OR '.join(keyword_conditions)})")

        where_clause = f"WHERE {' AND '.join(where_conditions)}"

        # Build SELECT fields
        select_fields = [
            "id",
            "title",
            "authors",
            "keywords",
            "folder_name",
            "abstract",
        ]

        if include_snippet:
            select_fields.append("SUBSTRING(abstract, 1, 200) as snippet")

        # Execute query
        query = f"""
        SELECT {", ".join(select_fields)}
        FROM papers 
        {where_clause}
        ORDER BY created_at DESC
        LIMIT %s
        """

        params.append(limit)

        async with self.pool.cursor() as cur:
            await cur.execute(query, params)
            results = await cur.fetchall()

            # Calculate match scores and matched keywords
            processed_results = []
            for r in results:
                doc_keywords = r["keywords"] or []

                # Find matched keywords
                matched_keywords = []
                for query_kw in keywords:
                    for doc_kw in doc_keywords:
                        if exact_match:
                            if case_sensitive:
                                if query_kw == doc_kw:
                                    matched_keywords.append(doc_kw)
                            else:
                                if query_kw.lower() == doc_kw.lower():
                                    matched_keywords.append(doc_kw)
                        else:
                            if case_sensitive:
                                if query_kw in doc_kw:
                                    matched_keywords.append(doc_kw)
                            else:
                                if query_kw.lower() in doc_kw.lower():
                                    matched_keywords.append(doc_kw)

                # Remove duplicates while preserving order
                matched_keywords = list(dict.fromkeys(matched_keywords))

                # Calculate match score
                match_score = len(matched_keywords) / len(keywords) if keywords else 0.0

                processed_results.append(
                    {
                        "id": r["id"],
                        "title": r["title"],
                        "authors": r["authors"],
                        "keywords": doc_keywords,
                        "matched_keywords": matched_keywords,
                        "match_score": match_score,
                        "snippet": r.get("snippet"),
                        "folder_name": r["folder_name"],
                        "abstract": r["abstract"],
                    }
                )

            # Sort by match score (highest first)
            processed_results.sort(key=lambda x: x["match_score"], reverse=True)
            return processed_results

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
        """
        Combined search using both text query and keywords.

        Args:
            text_query: Text to search in title/abstract
            keywords: Keywords to search for
            keyword_mode: "any" or "all" for keyword logic
            exact_keyword_match: Exact keyword matching
            folder_name: Optional folder filter
            filters: Additional metadata filters
            limit: Maximum results
            include_snippet: Include snippets

        Returns:
            Combined search results with relevance scoring
        """
        where_conditions = []
        params = []

        # Text search conditions
        text_conditions = []
        if text_query:
            text_query_lower = text_query.lower()
            text_conditions.append("(LOWER(title) LIKE %s OR LOWER(abstract) LIKE %s)")
            params.extend([f"%{text_query_lower}%", f"%{text_query_lower}%"])

        # Keyword search conditions
        keyword_conditions = []
        if keywords:
            if exact_keyword_match:
                if keyword_mode == "all":
                    for keyword in keywords:
                        keyword_conditions.append(
                            "LOWER(%s) = ANY(ARRAY(SELECT LOWER(unnest(keywords))))"
                        )
                        params.append(keyword.lower())
                else:
                    keyword_conditions.append(
                        "ARRAY(SELECT LOWER(unnest(keywords))) && %s"
                    )
                    params.append([kw.lower() for kw in keywords])
            else:
                # Fuzzy keyword matching
                if keyword_mode == "all":
                    for keyword in keywords:
                        keyword_conditions.append(
                            "EXISTS(SELECT 1 FROM unnest(keywords) AS kw WHERE LOWER(kw) LIKE %s)"
                        )
                        params.append(f"%{keyword.lower()}%")
                else:
                    kw_conditions = []
                    for keyword in keywords:
                        kw_conditions.append(
                            "EXISTS(SELECT 1 FROM unnest(keywords) AS kw WHERE LOWER(kw) LIKE %s)"
                        )
                        params.append(f"%{keyword.lower()}%")
                    keyword_conditions.append(f"({' OR '.join(kw_conditions)})")

        # Combine text and keyword conditions
        search_conditions = []
        if text_conditions:
            search_conditions.extend(text_conditions)
        if keyword_conditions:
            search_conditions.extend(keyword_conditions)

        if search_conditions:
            where_conditions.append(f"({' OR '.join(search_conditions)})")

        # Add other filters
        if folder_name:
            where_conditions.append("folder_name = %s")
            params.append(folder_name)

        if filters:
            for key, value in filters.items():
                if key == "year_of_publication":
                    where_conditions.append("publication_year = %s")
                    params.append(value)
                elif key in ["journal_name", "status"]:
                    where_conditions.append(f"{key} = %s")
                    params.append(value)

        # Build final query
        where_clause = (
            f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""
        )

        select_fields = [
            "id",
            "title",
            "authors",
            "keywords",
            "folder_name",
            "abstract",
            "1.0 as relevance_score",  # Basic relevance score
        ]

        if include_snippet:
            select_fields.append("SUBSTRING(abstract, 1, 200) as snippet")

        query = f"""
        SELECT {", ".join(select_fields)}
        FROM papers 
        {where_clause}
        ORDER BY created_at DESC
        LIMIT %s
        """

        params.append(limit)

        async with self.pool.cursor() as cur:
            await cur.execute(query, params)
            results = await cur.fetchall()

            return [
                {
                    "id": r["id"],
                    "title": r["title"],
                    "authors": r["authors"],
                    "keywords": r.get("keywords", []),
                    "relevance_score": float(r["relevance_score"]),
                    "snippet": r.get("snippet"),
                    "folder_name": r["folder_name"],
                    "abstract": r["abstract"],
                }
                for r in results
            ]

    async def get_all_keywords(
        self, folder_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all unique keywords from documents with their usage counts.

        Args:
            folder_name: Optional folder to limit scope

        Returns:
            List of keywords with usage statistics
        """
        where_conditions = ["keywords IS NOT NULL", "array_length(keywords, 1) > 0"]
        params = []

        if folder_name:
            where_conditions.append("folder_name = %s")
            params.append(folder_name)

        where_clause = (
            f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""
        )

        query = f"""
        SELECT 
            LOWER(keyword) as keyword,
            COUNT(*) as usage_count,
            COUNT(DISTINCT folder_name) as folder_count
        FROM papers 
        CROSS JOIN unnest(keywords) AS keyword
        {where_clause}
        GROUP BY LOWER(keyword)
        ORDER BY usage_count DESC, keyword ASC
        """

        async with self.pool.cursor() as cur:
            await cur.execute(query, params)
            results = await cur.fetchall()

            return [
                {
                    "keyword": r["keyword"],
                    "usage_count": r["usage_count"],
                    "folder_count": r["folder_count"],
                }
                for r in results
            ]
