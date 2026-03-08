"""
description_service.py
~~~~~~~~~~~~~~~~~~~~~~~
Generates a 4‑8 sentence search‑index description for a document using Gemini.
"""
import logging
import google.generativeai as genai
from app.core.config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


def generate_description(s3_key: str, content: str) -> str:
    """
    Summarise *content* (raw text from a DOCX / PDF) into a 4‑8 sentence
    description suitable for a keyword‑search index.

    Args:
        s3_key:  The S3 object key (used only for logging context).
        content: Decoded text content of the document.

    Returns:
        AI‑generated description string, or a short fallback if the API fails.
    """
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not configured")

    # Trim to ~4000 chars so we stay well within token limits
    snippet = content[:4000].strip()

    prompt = f"""You are a document librarian creating search‑index summaries.

Document key: {s3_key}

Document content (excerpt):
\"\"\"
{snippet}
\"\"\"

Write a concise description of this document in 4‑8 sentences.
Focus on:
- What type of content the document contains
- Key topics, ingredients, recipes, or procedures mentioned
- Any notable detail that would help someone searching for it

Return ONLY the description text — no headings, no bullet points, no extra commentary.
"""

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        description = response.text.strip()
        logger.info("[DescriptionService] Generated description for %s (%d chars)", s3_key, len(description))
        return description
    except Exception as exc:
        logger.error("[DescriptionService] Gemini call failed for %s: %s", s3_key, exc)
        raise
