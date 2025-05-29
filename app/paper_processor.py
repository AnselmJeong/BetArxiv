import logging
from typing import Optional, List
from uuid import UUID
import asyncio

from docling.document_converter import DocumentConverter
from ollama import AsyncClient as OllamaAsyncClient
import numpy as np

from .models import PaperCreate

logger = logging.getLogger(__name__)

OLLAMA_MODEL = "llama3.2"
OLLAMA_EMBED_MODEL = "llama3.2"  # or another embedding model if available


async def pdf_to_markdown(pdf_path: str) -> str:
    # Use docling to convert PDF to Markdown
    try:
        converter = DocumentConverter()
        result = converter.convert(pdf_path)
        markdown = result.document.export_to_markdown()
        return markdown
    except Exception as e:
        logger.error(f"Docling failed for {pdf_path}: {e}")
        raise


async def extract_metadata_and_sections(
    markdown: str, ollama_client: OllamaAsyncClient
) -> dict:
    # Use LLM to extract metadata and generate sections
    prompt = f"""
Given the following research paper in Markdown format, extract the following fields as JSON:
- title
- authors (as a list)
- journal name
- volume (issue no.)
- year of publication
- abstract
- keywords (as a list)

Markdown:
{markdown[:4000]}  # Truncate to avoid context overflow
"""
    try:
        response = await ollama_client.chat(
            model=OLLAMA_MODEL, messages=[{"role": "user", "content": prompt}]
        )
        import json

        data = json.loads(response["message"]["content"])
        return data
    except Exception as e:
        logger.error(f"LLM metadata extraction failed: {e}")
        raise


async def generate_sections(markdown: str, ollama_client: OllamaAsyncClient) -> dict:
    # Generate summary, distinction, methodology, results, implications
    sections = {}
    tasks = []
    prompts = {
        "summary": "Summarize the following research paper in 3-5 sentences.",
        "distinction": "What is the key distinction of this work compared to prior research?",
        "methodology": "Explain the methodology used in this paper.",
        "results": "Interpret the main results of the study.",
        "implications": "What are the implications of this study?",
    }
    for key, prompt in prompts.items():
        full_prompt = f"{prompt}\n\nMarkdown:\n{markdown[:4000]}"
        tasks.append(
            ollama_client.chat(
                model=OLLAMA_MODEL, messages=[{"role": "user", "content": full_prompt}]
            )
        )
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for key, res in zip(prompts.keys(), results):
        if isinstance(res, Exception):
            logger.error(f"LLM failed for {key}: {res}")
            sections[key] = None
        else:
            sections[key] = res["message"]["content"].strip()
    return sections


async def get_embedding(text: str, ollama_client: OllamaAsyncClient) -> List[float]:
    # Use Ollama to get embedding
    try:
        response = await ollama_client.embeddings(model=OLLAMA_EMBED_MODEL, prompt=text)
        return response["embedding"]
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        raise


async def process_pdf(pdf_path: str, ollama_client: OllamaAsyncClient) -> PaperCreate:
    markdown = await pdf_to_markdown(pdf_path)
    meta = await extract_metadata_and_sections(markdown, ollama_client)
    sections = await generate_sections(markdown, ollama_client)
    title_emb = await get_embedding(meta.get("title", ""), ollama_client)
    abstract_emb = await get_embedding(meta.get("abstract", ""), ollama_client)
    return PaperCreate(
        title=meta.get("title", "Unknown"),
        authors=meta.get("authors", []),
        journal_name=meta.get("journal_name"),
        volume_issue=meta.get("volume"),
        publication_year=meta.get("year"),
        abstract=meta.get("abstract"),
        keywords=meta.get("keywords", []),
        markdown=markdown,
        summary=sections.get("summary"),
        distinction=sections.get("distinction"),
        methodology=sections.get("methodology"),
        results=sections.get("results"),
        implications=sections.get("implications"),
        title_embedding=title_emb,
        abstract_embedding=abstract_emb,
        status="processed",
    )
