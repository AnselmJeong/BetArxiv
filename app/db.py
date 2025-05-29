import logging
from typing import List, Optional, Any
from uuid import UUID
from datetime import datetime

import psycopg
from psycopg.rows import dict_row

from .models import PaperCreate, Paper, PaperListItem

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

    async def insert_paper(self, paper: PaperCreate) -> UUID:
        query = """
        INSERT INTO papers (
            title, authors, journal_name, volume_issue, publication_year, abstract, keywords,
            markdown, summary, distinction, methodology, results, implications,
            title_embedding, abstract_embedding, status
        ) VALUES (
            %(title)s, %(authors)s, %(journal_name)s, %(volume_issue)s, %(publication_year)s, %(abstract)s, %(keywords)s,
            %(markdown)s, %(summary)s, %(distinction)s, %(methodology)s, %(results)s, %(implications)s,
            %(title_embedding)s, %(abstract_embedding)s, %(status)s
        ) RETURNING id;
        """
        async with self.pool.cursor() as cur:
            await cur.execute(query, paper.model_dump())
            row = await cur.fetchone()
            return row["id"]

    async def update_paper_status(self, paper_id: UUID, status: str):
        query = "UPDATE papers SET status=%s, updated_at=NOW() WHERE id=%s"
        async with self.pool.cursor() as cur:
            await cur.execute(query, (status, str(paper_id)))

    async def get_paper(self, paper_id: UUID) -> Optional[Paper]:
        query = "SELECT * FROM papers WHERE id=%s"
        async with self.pool.cursor() as cur:
            await cur.execute(query, (str(paper_id),))
            row = await cur.fetchone()
            if row:
                return Paper(**row)
            return None

    async def list_papers(
        self, page: int, per_page: int, search: Optional[str], year: Optional[int]
    ) -> (List[PaperListItem], int):
        offset = (page - 1) * per_page
        filters = []
        params: List[Any] = []
        if search:
            filters.append(
                "(LOWER(title) LIKE %s OR %s = ANY(LOWER(authors)) OR %s = ANY(LOWER(keywords)))"
            )
            s = f"%{search.lower()}%"
            params.extend([s, search.lower(), search.lower()])
        if year:
            filters.append("publication_year = %s")
            params.append(year)
        where = f"WHERE {' AND '.join(filters)}" if filters else ""
        count_query = f"SELECT COUNT(*) FROM papers {where}"
        query = f"""
            SELECT id, title, authors, journal_name, publication_year, abstract
            FROM papers {where}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        params_count = params.copy()
        params.extend([per_page, offset])
        async with self.pool.cursor() as cur:
            await cur.execute(count_query, params_count)
            total = (await cur.fetchone())["count"]
            await cur.execute(query, params)
            rows = await cur.fetchall()
            papers = [PaperListItem(**row) for row in rows]
            return papers, total

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
                    "total_papers": total,
                    "processed": processed,
                    "pending": pending,
                    "errors": errors,
                }
