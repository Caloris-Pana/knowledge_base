# Personal Knowledge Base — MCP Tool

A local semantic memory for AI agents (opencode). Stores problem-solution pairs persistently and retrieves them via semantic similarity search. Uses ChromaDB + `all-MiniLM-L6-v2` (local CPU, no API calls).

## Requirements

- **Python** >= 3.10
- **uv** or **pip** (setup.py auto-detects uv first, falls back to pip)
- **Network** on first run: downloads `all-MiniLM-L6-v2` (~80MB) embedding model from HuggingFace Hub

## Quick Start

```bash
git clone https://github.com/Caloris-Pana/knowledge_base.git
cd knowledge_base
python setup.py --yes
```

This installs dependencies, deploys `SKILL.md`, generates MCP config at `~/.config/opencode/opencode.jsonc`, and initializes the vector database. Run `python setup.py --help` for options.

## MCP Tools (used via opencode, never bypassed)

| Tool | Description |
|------|-------------|
| `save_solution(problem, solution, tags, context, cause, detail)` | Save a record. **Must** call `question` tool for user confirmation first. |
| `search_solutions(query, top_k=5)` | Semantic search across all records. |
| `list_solutions(limit=20, offset=0)` | View records list with summaries. |
| `get_solution(entry_id)` | View full detail of a single record. |
| `delete_solution(entry_id)` | Delete a record by ID. |

## Storage

- **Embedding model**: `all-MiniLM-L6-v2` (~80MB, cached on first use). Set `HF_HUB_OFFLINE=1` to skip hub check when offline.
- **Data dir**: `chroma_db/` — backup by copying this folder.
