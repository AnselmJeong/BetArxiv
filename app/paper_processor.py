import logging
from typing import Optional, List
from pathlib import Path
import os
import re

from docling.document_converter import DocumentConverter
from ollama import AsyncClient as OllamaAsyncClient
import numpy as np

from .models import DocumentCreate
from pydantic import BaseModel

logger = logging.getLogger(__name__)

OLLAMA_MODEL = "qwen3:14b"
OLLAMA_EMBED_MODEL = "nomic-embed-text"  # or another embedding model if available


class PaperMetadata(BaseModel):
    title: str
    authors: List[str]
    journal_name: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    year_of_publication: Optional[int] = None
    abstract: Optional[str] = None
    keywords: Optional[List[str]] = None


class PaperSummary(BaseModel):
    summary: str
    previous_work: str
    distinction: str
    methodology: str
    results: str
    implication: str


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


async def extract_metadata(markdown: str, ollama_client: OllamaAsyncClient) -> dict:
    # Use LLM to extract metadata and generate sections
    prompt = f"""
Given the following research paper in Markdown format, extract the following fields as JSON:
- title
- authors (as a list)
- journal_name
- volume
- issue
- year_of_publication
- abstract
- keywords (as a list)

Return only valid JSON matching this schema. Do not include any explanation or extra text.

Markdown:
{markdown[:4000]}
"""
    try:
        response = await ollama_client.chat(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": prompt}],
            format=PaperMetadata.model_json_schema(),
            think=False,
        )
        raw_content = response["message"]["content"]
        logger.debug(f"LLM raw response: {raw_content}")
        # Use Pydantic to parse and validate
        data = PaperMetadata.model_validate_json(raw_content).model_dump()
        return data
    except Exception as e:
        logger.error(f"LLM metadata extraction failed: {e}")
        raise


async def generate_summary(markdown: str, ollama_client: OllamaAsyncClient) -> dict:
    # Use a single LLM call to generate all sections in a structured format
    prompt = f"""
Please analyze the following academic paper thoroughly and provide structured responses to each of the following six aspects in necessary detail. 
Be precise, concise, and maintain an academic tone:
1. Summary: Summarize the entire research paper in 10-20 sentences. Focus on the core objective, approach, and findings.
2. Previous_Work: What is the theoretical background and related work in the field? Explain in detail so that even a beginner in this field can understand the background of why the paper was written.
3. Hypothesis: What is the hypothesis of the paper? and What problem is the paper trying to solve?
4. Distinction: What is the key distinction or novel contribution of this work compared to prior research in the same field?
5. Methodology: Describe the research design and methodology in detail, including participants (if any), tools, procedures, models, and any statistical analyses used.
6. Results: Interpret the main findings of the study. Highlight both statistical outcomes and any figures/tables if they are crucial. 
7. Limitation: What are the limitations of the study?
8. Implication: Explain the broader implications of this study for theory, practice, or future research directions.

Return only valid JSON matching this schema. Do not include any explanation or extra text except for the JSON.

Markdown:
{markdown}
"""
    try:
        response = await ollama_client.chat(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": prompt}],
            format=PaperSummary.model_json_schema(),
            think=False,
        )
        raw_content = response["message"]["content"]
        logger.debug(f"LLM raw response (summary): {raw_content}")
        data = PaperSummary.model_validate_json(raw_content).model_dump()
        return data
    except Exception as e:
        logger.error(f"LLM section extraction failed: {e}")
        raise


async def get_embedding(text: str, ollama_client: OllamaAsyncClient) -> List[float]:
    # Use Ollama to get embedding
    try:
        response = await ollama_client.embeddings(model=OLLAMA_EMBED_MODEL, prompt=text)
        return response["embedding"]
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        raise


async def process_pdf(pdf_path: str, ollama_client: OllamaAsyncClient) -> DocumentCreate:
    """Process a PDF file and extract metadata, content, and generate embeddings"""
    pdf_file = Path(pdf_path)

    # Extract folder name from the path
    base_dir = os.getenv("DIRECTORY", ".")
    try:
        folder_name = str(pdf_file.parent.relative_to(Path(base_dir)))
        if folder_name == ".":
            folder_name = None
    except ValueError:
        # PDF is outside the base directory
        folder_name = str(pdf_file.parent)

    markdown = await pdf_to_markdown(pdf_path)
    # Remove references section and everything after (robust heading/line match)
    pattern = re.compile(
        r"^(#{1,6}\s*)?(references|reference|bibliography|참고문헌)\s*$",
        re.IGNORECASE | re.MULTILINE,
    )
    match = pattern.search(markdown)
    if match:
        markdown = markdown[: match.start()].rstrip()

    meta = await extract_metadata(markdown, ollama_client)
    summary = await generate_summary(markdown, ollama_client)
    title_emb = await get_embedding(meta.get("title", ""), ollama_client)
    abstract_emb = await get_embedding(meta.get("abstract", ""), ollama_client)

    return DocumentCreate(
        title=meta.get("title", "Unknown"),
        authors=meta.get("authors", []),
        journal_name=meta.get("journal_name"),
        publication_year=meta.get("year_of_publication"),
        abstract=meta.get("abstract"),
        keywords=meta.get("keywords", []),
        markdown=markdown,
        summary=summary.get("summary"),
        previous_work=summary.get("previous_work"),
        distinction=summary.get("distinction"),
        methodology=summary.get("methodology"),
        results=summary.get("results"),
        implications=summary.get("implication"),
        title_embedding=title_emb,
        abstract_embedding=abstract_emb,
        status="processed",
        folder_name=folder_name,
        url=str(pdf_file),  # Store the full file path
    )
