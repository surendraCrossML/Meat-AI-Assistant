"""
mcp_server/server.py
~~~~~~~~~~~~~~~~~~~~~
Standalone MCP (Model Context Protocol) server for the Meat AI Assistant.

Exposes one tool:
  • query_documents — wraps POST /documents/query and returns the full
    structured JSON response, letting any MCP host (Claude Desktop, Cursor,
    etc.) search and query the document store using natural language.

Usage
-----
  # Dev mode — opens MCP Inspector in the browser
  mcp dev mcp_server/server.py

  # Production / stdio transport (add to Claude Desktop config)
  python mcp_server/server.py

Transport: stdio  (compatible with all MCP hosts)
"""

import json
import logging
import argparse

import httpx
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

# FastAPI backend URL
BASE_URL = "http://127.0.0.1:8000"
QUERY_ENDPOINT = f"{BASE_URL}/documents/query"
LIST_ENDPOINT  = f"{BASE_URL}/documents/"

# MCP Server
mcp = FastMCP(
    name="Meat AI Assistant",
    host="0.0.0.0",
    instructions=(
        "Use this server to search and query beef / meat recipe documents "
        "stored in the Meat AI Assistant knowledge base. "
        "Call `query_documents` with a natural-language question to get "
        "an AI-generated answer grounded in the document store."
    ),
)


# Tool 1: query_documents
@mcp.tool()
async def query_documents(query: str) -> str:
    """
    Search the Meat AI Assistant document store using a natural-language query.

    The tool:
    1. Sends the query to the backend API.
    2. The API uses Gemini AI to extract keywords and find matching documents.
    3. Matched documents are downloaded from S3 and passed to Gemini to
       generate a grounded answer.
    4. The full structured response is returned as JSON.

    Args:
        query: A natural-language question or search intent, e.g.
               "What are the best beef recipes for a healthy diet?"

    Returns:
        JSON string containing:
          - user_query            : echoed back
          - extracted_keywords    : keywords Gemini extracted from the query
          - matching_documents    : list of documents found in the DB
          - summary               : short match summary
          - agent_response        : AI-generated answer from document content
    """
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(QUERY_ENDPOINT, json={"query": query})
            resp.raise_for_status()
            data = resp.json()

        return json.dumps(data, indent=2, ensure_ascii=False)

    except httpx.HTTPStatusError as exc:
        error = {
            "error": f"Backend returned HTTP {exc.response.status_code}",
            "detail": exc.response.text,
        }
        logger.error("[MCP] query_documents HTTP error: %s", error)
        return json.dumps(error, indent=2)

    except Exception as exc:
        error = {"error": str(exc)}
        logger.error("[MCP] query_documents unexpected error: %s", exc)
        return json.dumps(error, indent=2)


# Tool 2: list_documents
@mcp.tool()
async def list_documents() -> str:
    """
    List all documents currently stored in the Meat AI Assistant knowledge base.

    Returns:
        JSON array of document metadata (id, name, type, size, description,
        s3_key, created_at).
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(LIST_ENDPOINT)
            resp.raise_for_status()
            data = resp.json()

        return json.dumps(data, indent=2, ensure_ascii=False)

    except httpx.HTTPStatusError as exc:
        error = {
            "error": f"Backend returned HTTP {exc.response.status_code}",
            "detail": exc.response.text,
        }
        return json.dumps(error, indent=2)

    except Exception as exc:
        return json.dumps({"error": str(exc)}, indent=2)


# Entry point
if __name__ == "__main__":
    mcp.run(transport="stdio")
