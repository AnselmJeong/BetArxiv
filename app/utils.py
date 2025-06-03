import numpy as np
import os
import logging
import asyncio
from typing import List, Optional
from pathlib import Path
import io
from PIL import Image
from pdf2image import convert_from_path

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

logger = logging.getLogger(__name__)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_EMBED_MODEL = "gemini-embedding-exp-03-07"
GEMINI_CHAT_MODEL = "gemini-2.0-flash-exp"


def get_genai_client():
    """Get configured Google Generative AI client"""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable is required")

    genai.configure(api_key=api_key)
    return genai


async def get_embedding(text: str, client) -> List[float]:
    """Generate embedding for text using Google's embedding model"""
    try:
        # Use the embedding model
        model = "models/embedding-001"
        response = await asyncio.to_thread(
            genai.embed_content,
            model=model,
            content=text,
            task_type="retrieval_document",
        )
        return response["embedding"]
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        raise


async def chat_with_document_content(
    title: str,
    authors: List[str],
    markdown_content: str,
    user_message: str,
    genai_client,
) -> str:
    """Generate a chat response based on document content using Google Gemini"""
    try:
        # Create context prompt with document information
        context_prompt = f"""
You are an AI assistant helping users understand an academic paper. Here is the paper information:

Title: {title}
Authors: {", ".join(authors)}

Paper Content:
{markdown_content}

User Question: {user_message}

Please provide a helpful and accurate response based on the paper content. If the question cannot be answered from the provided content, please say so clearly.
"""

        # Use Gemini 2.0 Flash model for chat
        model = genai.GenerativeModel("gemini-2.0-flash-exp")

        # Generate response
        response = await asyncio.to_thread(
            model.generate_content,
            context_prompt,
            safety_settings={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            },
        )

        return response.text

    except Exception as e:
        logger.error(f"Error in chat completion: {e}")
        raise


def generate_pdf_thumbnail(
    pdf_path: Path, width: int = 400, height: int = 280
) -> io.BytesIO:
    """
    Generate a thumbnail image from the first page of a PDF file.
    Maintains aspect ratio within the given maximum dimensions.

    Args:
        pdf_path: Path to the PDF file
        width: Maximum thumbnail width
        height: Maximum thumbnail height

    Returns:
        BytesIO object containing the thumbnail image
    """
    try:
        # Convert first page of PDF to image with higher DPI for better quality
        images = convert_from_path(pdf_path, first_page=1, last_page=1, dpi=300)

        if not images:
            raise ValueError("Could not extract any pages from PDF")

        pdf_image = images[0]

        # Calculate crop area (top portion of the page)
        img_width, img_height = pdf_image.size

        # Use top 40% of the page for thumbnail
        crop_height = int(img_height * 0.4)
        crop_box = (0, 0, img_width, crop_height)

        # Crop the image
        cropped_image = pdf_image.crop(crop_box)

        # Calculate aspect ratio preserving resize
        original_width, original_height = cropped_image.size
        aspect_ratio = original_width / original_height

        # Calculate new dimensions maintaining aspect ratio
        if width / height > aspect_ratio:
            # Height is the limiting factor
            new_height = height
            new_width = int(height * aspect_ratio)
        else:
            # Width is the limiting factor
            new_width = width
            new_height = int(width / aspect_ratio)

        # Resize to calculated dimensions with high quality resampling
        thumbnail = cropped_image.resize(
            (new_width, new_height), Image.Resampling.LANCZOS
        )

        # Convert to RGB if necessary (PDF images might be in different modes)
        if thumbnail.mode != "RGB":
            thumbnail = thumbnail.convert("RGB")

        # Save to BytesIO with higher quality
        img_buffer = io.BytesIO()
        thumbnail.save(img_buffer, format="JPEG", quality=95, optimize=True)
        img_buffer.seek(0)

        return img_buffer

    except Exception as e:
        logger.error(f"Error generating PDF thumbnail: {e}")
        raise


def cosine_similarity(vec1, vec2):
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))
