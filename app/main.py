import asyncio
import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from contextlib import asynccontextmanager

from .db import Database
from .api import get_router
from ollama import AsyncClient as OllamaAsyncClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# def parse_args():
#     parser = argparse.ArgumentParser(
#         description="Research Paper Knowledge Extraction API"
#     )
#     parser.add_argument(
#         "--directory",
#         type=str,
#         default=os.getenv("DIRECTORY", "."),
#         help="Directory to monitor for PDFs",
#     )
#     parser.add_argument(
#         "--db-url",
#         type=str,
#         default=os.getenv("DATABASE_URL"),
#         help="PostgreSQL connection string",
#     )
#     return parser.parse_args()


# args = parse_args()
load_dotenv()

DB_URL = os.getenv("DATABASE_URL")
if not DB_URL:
    raise ValueError("DATABASE_URL environment variable is not set. Please create a .env file or set it directly.")
MONITOR_DIRECTORY = os.getenv("DIRECTORY", ".")

# Initialize database and Ollama client
db = Database(DB_URL)
ollama_client = OllamaAsyncClient()

# Create FastAPI app
app = FastAPI(
    title="Research Paper Knowledge Extraction API",
    description="Extracts, summarizes, and searches research papers using LLMs and PostgreSQL.",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the router with prefix
app.include_router(get_router(db, ollama_client, None), prefix="/api")


# Add a test endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to the Research Paper Knowledge Extraction API"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    if not hasattr(app.state, "db"):
        await db.connect()
        app.state.db = db
    logger.info("Application startup complete.")
    try:
        yield
    finally:
        # Shutdown
        if hasattr(app.state, "db"):
            await app.state.db.close()
        logger.info("Application shutdown complete.")


# Set the lifespan
app.lifespan = lifespan


# @app.on_event("startup")
# async def startup_event():
#     await db.connect()
#     app.include_router(get_router(db, ollama_client, pdf_queue))
#     # Start directory watcher in background
#     loop = asyncio.get_event_loop()
#     loop.create_task(start_watcher(args.directory, pdf_queue))
#     loop.create_task(pdf_processing_worker())


# @app.on_event("shutdown")
# async def shutdown_event():
#     await db.close()
#     await ollama_client.aclose()


# async def pdf_processing_worker():
#     while True:
#         pdf_path = await pdf_queue.get()
#         try:
#             from .paper_processor import process_pdf

#             document_data = await process_pdf(pdf_path, ollama_client)
#             document_id = await db.insert_document(document_data)
#             await db.update_paper_status(document_id, "processed")
#             logger.info(f"Processed and stored document: {document_id}")
#         except Exception as e:
#             logger.error(f"Failed to process {pdf_path}: {e}")
#         finally:
#             pdf_queue.task_done()
