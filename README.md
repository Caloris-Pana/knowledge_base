# Personal Knowledge Base — MCP Tool

A local semantic memory for AI agents (opencode). Stores problem-solution pairs persistently and retrieves them via semantic similarity search.

## Architecture

```
User → opencode → MCP(kb_server.py) → ChromaDB + sentence-transformers(本地嵌入模型)
```

- **ChromaDB** (vector database): persists all data to `chroma_db/`
- **sentence-transformers** (`all-MiniLM-L6-v2`): runs locally on CPU, no API calls
- **MCP server** (`kb_server.py`): JSON-RPC over stdio, automatically launched by opencode

## Exposed Tools

### `save_solution(problem, solution, tags, context="", cause="", detail="")`

Persist a new problem-solution pair. Must only be called after user confirms via `question` tool (按钮选择).

| Field | Type | Description |
|-------|------|-------------|
| `problem` | `str` | Short title (e.g. "ZED camera init fail with error -1") |
| `solution` | `str` | Step-by-step solution |
| `tags` | `list[str]` | For filtering/classification (e.g. `["zed", "camera", "hardware"]`) |
| `context` | `str` | Environment info (e.g. "Jetson Orin AGX, JetPack L4T r36.4.0") |
| `cause` | `str` | Root cause of the problem (e.g. "USB power insufficient, xda daemon cannot enumerate device") |
| `detail` | `str` | Full error message, reproduction steps, extra notes |

### `delete_solution(entry_id)`

Delete a record by ID. Direct operation, no confirmation required.

| Field | Type | Description |
|-------|------|-------------|
| `entry_id` | `str` | Record ID to delete |

### `list_solutions(limit=20, offset=0)`

View all records with summary. Returns `{total, records[]}`. Each record includes `order` and `problem`.

### `get_solution(entry_id)`

View full detail of a single record. Returns all fields: `problem`, `cause`, `solution`, `tags`, `context`, `detail`, `timestamp`.

### `search_solutions(query, top_k=5)`

Semantic search across the knowledge base. Returns top-K results with similarity score (cosine distance → 0%~100%).

## Save Workflow

This is the ONLY correct way to save data. The MCP tool itself writes ONLY to `chroma_db/` and does NOT create any extra files anywhere in the workspace.

**保存流程不执行任何相似记录检查。** agent 调用 `save_solution` 前不得调用 `search_solutions` 查重。此约束记录在 `.opencode/skills/knowledge-base/SKILL.md` 中。

### Step-by-step

```
① 用户: "把这个问题的解法存到知识库"
         ↓
② Agent 分析对话 → 提炼结构化内容
   (problem, cause, solution, tags, context, detail)
         ↓
③ Agent 调用 question 工具，展示预览并提供三个按钮:

   ┌──────────────────────────────────────────────────┐
   │  即将存入知识库：                                  │
   │                                                   │
   │  问题: Docker 容器时区在宿主机修改时区后未同步     │
   │  原因: 容器只创建时继承时区，宿主机变更不会同步    │
   │  方案: 1. 添加 -v /etc/timezone:/etc/timezone:ro  │
   │        2. 或通过 -e TZ=Asia/Shanghai              │
   │        3. 已有容器需重建                          │
   │  标签: docker, timezone, jetson, container        │
   │  环境: Jetson Orin AGX, Docker                    │
   │                                                   │
   │    [确认存入]    [修改内容]    [取消]              │
   └──────────────────────────────────────────────────┘
         ↓
④ 用户操作:
   确认存入 → Agent 调用 save_solution 写入 chroma_db/
   修改内容 → 用户打字告诉 Agent 要改什么 → 调整后回到步骤③
   取消     → 丢弃，不写入，无任何副作用
         ↓
⑤ 保存成功 → Agent 回复 "✅ 已存入知识库 (ID: xxx)"
```

### No side effects

验证结果：`save_solution` 调用全程只读写 `knowledge_base/chroma_db/`，不会在 `tmp_logs/` 或任何其他目录生成文件。

**出现 `tmp_logs/` 下脚本文件的原因：** 之前另一个对话中的 agent 发现 MCP 工具未暴露，选择手写 Python 脚本（`save_kb.py` 等）绕道调用 `ingest.py` 和 `query.py` 实现保存和搜索。SKILL.md 已新增约束：**禁止手写替代脚本**，MCP 不可用时直接报告问题。

## Storage Details

- **Embedding model**: `all-MiniLM-L6-v2` (384-dim vectors, ~80MB, cached at first use)
- **Distance metric**: cosine
- **Data dir**: `knowledge_base/chroma_db/` (backup by copying this folder)

## CLI Usage (maintenance)

For maintenance tasks via terminal, use `cli.py` with JSON files to avoid PowerShell encoding issues:

```bash
# Save
echo '{"problem":"...","solution":"...","tags":[]}' > record.json
python cli.py save --file record.json

# List
python cli.py list

# Get detail
python cli.py get --id <entry_id>

# Delete
python cli.py delete --id <entry_id>

# Search
python cli.py search --file query.json
```

Set `HF_HUB_OFFLINE=1` to skip HuggingFace Hub check when offline.

## Agent Usage Examples

| User says | Agent action |
|-----------|-------------|
| "把这个问题的解法存到知识库" | Extract problem/solution from conversation → show via `question` with [确认存入/修改内容/取消] → if confirm, call `save_solution` |
| "查一下之前 ZED 的问题怎么解决的" | Call `search_solutions("ZED ...")` → show results |
| "把这个测试记录存到知识库" | Same workflow: preview → question → save_solution |
| "查看知识库" | Call `list_solutions()` → show numbered list of problems |
| "查看第 2 条详情" | Get ID from list → call `get_solution(id)` → show full content |
| "删除第 3 条记录" | Get ID from list → call `delete_solution(id)` → confirm |
