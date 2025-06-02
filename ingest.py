import warnings

import os
import asyncio
from pathlib import Path
import argparse
import traceback
from tqdm import tqdm
import dotenv


# Import your app's database and processing logic
from app.db import Database
from app.paper_processor import process_pdf
from ollama import AsyncClient as OllamaAsyncClient


dotenv.load_dotenv()

warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=UserWarning)


DSN = os.getenv("DATABASE_URL")  # Adjust as needed


async def get_all_pdf_paths(base_dir):
    return [str(p) for p in Path(base_dir).rglob("*.pdf")]


async def get_already_ingested_paths(db):
    # Query all URLs (file paths) from the DB
    query = "SELECT url FROM documents WHERE url IS NOT NULL"
    async with db.pool.cursor() as cur:
        await cur.execute(query)
        rows = await cur.fetchall()
        return set(row["url"] for row in rows if row["url"])


async def main(data_root):
    print(f"[DEBUG] Using DATABASE_URL: {DSN}")
    db = Database(DSN)
    await db.connect()
    ollama_client = OllamaAsyncClient()
    all_pdfs = set(await get_all_pdf_paths(data_root))
    print(f"[DEBUG] Found {len(all_pdfs)} PDFs in '{data_root}' (including subdirectories)")
    already_ingested = set(await get_already_ingested_paths(db))
    print(f"[DEBUG] Found {len(already_ingested)} already-ingested PDFs in DB")
    new_pdfs = all_pdfs - already_ingested

    if not new_pdfs:
        print("No new PDFs to ingest.")
        await db.close()
        return

    print(f"Found {len(new_pdfs)} new PDFs to ingest in '{data_root}'.")
    for pdf_path in tqdm(sorted(new_pdfs), desc="Ingesting PDFs"):
        try:
            document_data = await process_pdf(pdf_path, ollama_client)
            document_id = await db.insert_document(document_data)
            await db.update_paper_status(document_id, "processed")
            # print(f"✅ Ingested: {pdf_path} (ID: {document_id})")
        except Exception as e:
            print(f"❌ Failed to ingest {pdf_path}: {e}")
            traceback.print_exc()

    await db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest new PDFs from a data root directory.")
    parser.add_argument(
        "--directory",
        "-d",
        type=str,
        default="docs",
        help="Root directory to scan for PDFs (default: 'docs')",
    )
    args = parser.parse_args()
    asyncio.run(main(args.directory))
