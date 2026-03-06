# Meat AI Assistant — MCP Server

## Overview

The MCP server exposes the Meat AI Assistant document store as an **MCP tool**, letting any MCP-compatible AI host (Claude Desktop, Cursor, Windsurf, etc.) search and query your beef-recipe document library using natural language.

### Exposed Tools

| Tool              | Description                                                          |
| ----------------- | -------------------------------------------------------------------- |
| `query_documents` | Natural-language search + AI-generated answer from matched documents |
| `list_documents`  | List all documents in the knowledge base                             |

---

## Prerequisites

- FastAPI backend running at `http://127.0.0.1:8000`
- Python venv activated with `mcp[cli]` installed

```bash
cd /path/to/Meat-AI-Assistant
source venv/bin/activate
pip install "mcp[cli]"
```

---

## Running the MCP Server

### Dev Mode (MCP Inspector in browser)

```bash
cd /home/surendrasingh/Videos/Meat-AI-Assistant
source venv/bin/activate
mcp dev mcp_server/server.py
```

Then open the Inspector URL printed in the terminal, select a tool, and run it.

### Direct (stdio)

```bash
python mcp_server/server.py
```

---

## Claude Desktop Integration

Add this block to `~/.config/claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "meat-ai-assistant": {
      "command": "/home/surendrasingh/Videos/Meat-AI-Assistant/venv/bin/python",
      "args": [
        "/home/surendrasingh/Videos/Meat-AI-Assistant/mcp_server/server.py"
      ]
    }
  }
}
```

Restart Claude Desktop. The `query_documents` and `list_documents` tools will appear automatically.

---

## Cursor Integration

Add to `.cursor/mcp.json` in your project root:

```json
{
  "mcpServers": {
    "meat-ai-assistant": {
      "command": "/home/surendrasingh/Videos/Meat-AI-Assistant/venv/bin/python",
      "args": [
        "/home/surendrasingh/Videos/Meat-AI-Assistant/mcp_server/server.py"
      ]
    }
  }
}
```

---

## Example Tool Call

**Tool:** `query_documents`
**Input:**

```json
{ "query": "What are the best beef recipes for a healthy diet?" }
```

**Output** (abbreviated):

```json
{
  "user_query": "What are the best beef recipes for a healthy diet?",
  "extracted_keywords": { "keywords": ["beef", "recipes", "healthy", "diet"] },
  "matching_documents": [ ... ],
  "agent_response": "Based on the documents ..."
}
```
