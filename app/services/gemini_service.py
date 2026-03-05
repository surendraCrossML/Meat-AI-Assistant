import json
import google.generativeai as genai
from app.core.config import GEMINI_API_KEY


if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


def extract_keywords_from_query(user_query: str) -> dict:
    """
    Extract keywords related to recipes and beef from user query using Gemini AI.
    
    Args:
        user_query: User's natural language query
        
    Returns:
        Dictionary containing:
        - keywords: List of extracted keywords
        - recipe_related_keywords: Keywords specifically related to recipes
        - beef_related_keywords: Keywords specifically related to beef
        - query_summary: Brief summary of what the user is asking
    """
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not configured")
    
    prompt = f"""
    Extract keywords from the following user query about recipes and beef products.
    
    User Query: "{user_query}"
    
    Please analyze this query and return a JSON response with the following structure:
    {{
        "keywords": [list of all relevant keywords],
        "recipe_related_keywords": [keywords related to cooking, preparation, dishes],
        "beef_related_keywords": [keywords related to beef, meat types, cuts],
        "query_summary": "a brief one-line summary of what the user is looking for"
    }}
    
    Focus on extracting concrete, searchable terms that would help find relevant documents.
    Be comprehensive but concise. Return only valid JSON.
    """
    
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)
    
    try:
        # Extract JSON from response
        response_text = response.text
        
        # Try to parse the JSON
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_str = response_text.split("```")[1].split("```")[0].strip()
        else:
            json_str = response_text.strip()
        
        result = json.loads(json_str)
        return result
    except json.JSONDecodeError:
        # Fallback: return the raw response
        return {
            "keywords": user_query.split(),
            "recipe_related_keywords": [],
            "beef_related_keywords": [],
            "query_summary": user_query
        }


def refine_search_query(keywords: list, user_query: str) -> str:
    """
    Use Gemini to create an optimized search query from extracted keywords.
    
    Args:
        keywords: List of extracted keywords
        user_query: Original user query
        
    Returns:
        str: Optimized search query
    """
    if not GEMINI_API_KEY:
        return " ".join(keywords)
    
    prompt = f"""
    Given these keywords: {', '.join(keywords)}
    And the original query: "{user_query}"
    
    Create a concise search query (max 10 words) that best captures what the user is looking for.
    Return only the search query, nothing else.
    """
    
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(prompt)
    return response.text.strip()



def generate_response_from_documents(user_query: str, documents: list[dict]) -> str:
    """
    Use Gemini to answer the user's query based on the actual content of matched documents.

    Args:
        user_query: The user's natural language question.
        documents: List of dicts, each with keys:
            - 'document_name' (str)
            - 'content'       (str) — full text fetched from S3

    Returns:
        A helpful answer grounded only in the provided documents.
    """
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not configured")

    if not documents:
        return "No matching documents were found to answer your question."

    # Build a clearly labelled context block for the LLM
    context_parts = []
    for i, doc in enumerate(documents, start=1):
        name = doc.get("document_name", f"Document {i}")
        content = doc.get("content", "").strip()
        context_parts.append(
            f"--- Document {i}: {name} ---\n{content}\n"
        )
    context_text = "\n".join(context_parts)

    prompt = f"""You are a helpful assistant that answers questions strictly based on the provided documents.

DOCUMENTS:
{context_text}

USER QUESTION:
{user_query}

Instructions:
- Answer the question using ONLY the information found in the documents above.
- Be specific, practical, and helpful.
- If the documents contain relevant recipes, steps, or tips, include them in your answer.
- If the documents do not contain enough information to answer the question, say so clearly.
- Do not reference external sources or make up information.
"""

    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)
    return response.text.strip()
