# AGENTS.md — Knowledge Base MCP Server

## Repo structure

```
setup.py              — deployment script (install deps, config, init kb)
kb_server.py          — MCP entrypoint (5 tools via FastMCP)
scripts/
  ingest.py           — chromadb write ops (add_solution, delete_solution)
  query.py            — chromadb read ops + kb_not_found guard
  model.py            — all-MiniLM-L6-v2 singleton loader
cli.py                — maintenance CLI (data via JSON files)
config/               — reference config examples (SKILL.md, MCP example)
AGENTS.md             — this file (agent guidelines)
.opencode/skills/knowledge-base/SKILL.md  — agent behavioral constraints
chroma_db/            — vector store data (gitignored)
```

## How it runs

- **Not a web app.** Runs as `python kb_server.py` via opencode MCP stdio transport.
- **Virtualenv** is at `../TMS_dev/knowledge_base/.venv/` (outside this repo). `.venv/` is gitignored.
- **Python 3.14.4**, dependencies: chromadb, sentence-transformers, mcp (see `requirements.txt`).

## MCP tools (used via MCP, never bypassed)

| Tool | Key notes |
|------|-----------|
| `save_solution` | Requires `question` confirmation first. **No duplicate check.** |
| `list_solutions` | Returns `kb_not_found: true` if `chroma_db/` missing. |
| `search_solutions` | Semantic search. Empty collection → `[]`. |
| `get_solution` | Missing ID → `None`. |
| `delete_solution` | Missing ID → silent no-op. |

## Critical agent constraints (from SKILL.md)

- **Must use `question` tool** before calling `save_solution` — preview with [确认存入/修改内容/取消]
- **No duplicate check** — do not call `search_solutions` before save
- **Never write bypass scripts** — if MCP is broken, report it, don't call `ingest.py`/`query.py` directly
- **No side effects** — save only writes to `chroma_db/`

## CLI (maintenance only — not for agent use)

```bash
python cli.py save --file record.json     # JSON: problem, solution, tags[]
python cli.py list [--limit 20] [--offset 0]
python cli.py get --id <uuid>
python cli.py delete --id <uuid>
python cli.py search --file query.json     # JSON: query, top_k
```

All data via UTF-8 JSON files (PowerShell pipe encoding issue).

## Other

- **No test/lint/build infrastructure** — no pytest, no ruff, no typecheck.
- **`chroma_db/` is data, not code** — gitignored. Backup by copying the folder.
- **Embedding model** (~80MB) downloads on first `get_model()` call. Set `HF_HUB_OFFLINE=1` to skip hub check when offline.
- **Ubuntu WSL path**: `~/Desktop/TMS_dev/knowledge_base/chroma_db/` when accessed from WSL.
