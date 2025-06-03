import numpy as np
import os
import logging
from typing import List
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_EMBED_MODEL = "gemini-embedding-exp-03-07"
GEMINI_CHAT_MODEL = "gemini-2.0-flash-exp"


def get_genai_client():
    """Get Google GenAI client"""
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY environment variable is not set")
    return genai.Client(api_key=GOOGLE_API_KEY)


async def get_embedding(text: str, genai_client: genai.Client) -> List[float]:
    """Use Google GenAI to get embedding"""
    try:
        response = await genai_client.aio.models.embed_content(
            model=GEMINI_EMBED_MODEL,
            contents=text,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_QUERY",  # Use RETRIEVAL_QUERY for search queries
                output_dimensionality=768,
            ),
        )
        embeddings = response.embeddings[0].values
        return embeddings
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        # Fallback: return a zero vector of the expected dimension
        return [0.0] * 768


async def chat_with_document_content(
    title: str,
    authors: List[str],
    markdown_content: str,
    user_message: str,
    genai_client: genai.Client,
) -> str:
    """Generate a response based on document content and user question"""
    try:
        # Create a context prompt with document content
        context_prompt = f"""You are an AI assistant helping users understand a research paper. Here is the document information:

Title: {title}
Authors: {", ".join(authors)}

Document Content:
{markdown_content}

Please answer the user's question based on the document content above. Be specific and cite relevant parts of the paper when possible.

User Question: {user_message}

Answer:"""

        response = await genai_client.aio.models.generate_content(
            model=GEMINI_CHAT_MODEL,
            contents=context_prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=1000,
                temperature=0.3,  # Lower temperature for more focused responses
            ),
        )

        return response.text.strip()
    except Exception as e:
        logger.error(f"Chat generation failed: {e}")
        return "I'm sorry, I encountered an error while processing your question. Please try again."


def cosine_similarity(vec1, vec2):
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))
