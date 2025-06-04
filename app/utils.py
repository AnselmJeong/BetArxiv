import numpy as np
import os
import logging
import asyncio
from pathlib import Path
import io
import json
from typing import List, Optional
from pydantic import BaseModel, ValidationError
from PIL import Image
from pdf2image import convert_from_path

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

logger = logging.getLogger(__name__)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_EMBED_MODEL = "gemini-embedding-exp-03-07"
GEMINI_CHAT_MODEL = "gemini-2.5-flash-preview-05-20"


class PaperSummary(BaseModel):
    summary: str
    previous_work: str
    hypothesis: str
    distinction: str
    methodology: str
    results: str
    limitations: str
    implication: str


def get_genai_client():
    """Get configured Google Generative AI client"""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable is required")

    genai.configure(api_key=api_key)
    return genai


async def get_embedding(text: str, client) -> list[float]:
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
    authors: list[str],
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
        model = genai.GenerativeModel(GEMINI_CHAT_MODEL)

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


async def generate_summary(markdown: str, genai_client) -> dict:
    """Use a single LLM call to generate all sections in a structured format"""
    prompt = f"""
Please analyze the following academic paper thoroughly and provide structured responses to each of the following aspects in necessary detail. 
Be precise, concise and focused on the key points for the reader to understand the paper, and maintain an academic tone.
If needed, use bullet points and markdown formatting to make each section more readable.

Provide your response as JSON with exactly these fields:
1. "summary": Summarize the entire research paper in 10-20 sentences. Focus on the core objective, approach, and findings.
2. "previous_work": What is the theoretical background and related work in the field? Explain in detail so that even a beginner in this field can understand the background of why the paper was written.
3. "hypothesis": What is the hypothesis of the paper? and What problem is the paper trying to solve?
4. "distinction": What is the key distinction or novel contribution of this work compared to prior research in the same field?
5. "methodology": Describe the research design and methodology in detail, including participants (if any), tools, procedures, models, and any statistical analyses used.
6. "results": Interpret the main findings of the study. Highlight statistical outcomes if they are crucial. 
7. "limitations": What are the limitations of the study?
8. "implication": Explain the broader implications of this study for theory, practice, or future research directions.

Return only valid JSON matching this schema. Do not include any explanation or extra text except for the JSON.

Markdown:
{markdown}
"""

    # Default values in case of extraction failure
    default_summary = {
        "summary": "Summary not available due to processing error.",
        "previous_work": "Previous work analysis not available.",
        "hypothesis": "Hypothesis not available.",
        "distinction": "Distinction analysis not available.",
        "methodology": "Methodology not available.",
        "results": "Results not available.",
        "limitations": "Limitations not available.",
        "implication": "Implications not available.",
    }

    try:
        # Use Gemini model for summary generation
        model = genai.GenerativeModel(
            GEMINI_CHAT_MODEL,
            generation_config={
                "response_mime_type": "application/json",
            },
        )

        response = await asyncio.to_thread(
            model.generate_content,
            prompt,
            safety_settings={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            },
        )

        raw_content = response.text
        logger.debug(f"LLM raw response (summary): {raw_content}")

        # Try to validate with Pydantic
        try:
            data = PaperSummary.model_validate_json(raw_content).model_dump()
            logger.info("✅ Summary extraction successful")
            return data
        except (ValidationError, json.JSONDecodeError) as validation_error:
            logger.warning(
                f"⚠️ Summary JSON validation failed, trying to parse manually: {validation_error}"
            )

            # Try to parse JSON manually and extract what we can
            try:
                raw_data = json.loads(raw_content)
                extracted_data = {}
                for key in default_summary.keys():
                    extracted_data[key] = raw_data.get(key, default_summary[key])

                logger.info("✅ Partial summary extraction successful")
                return extracted_data

            except json.JSONDecodeError:
                logger.warning("⚠️ Could not parse summary JSON at all, using defaults")
                return default_summary

    except Exception as e:
        logger.error(f"❌ LLM summary extraction failed completely: {e}")
        return default_summary


def cosine_similarity(vec1, vec2):
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))
