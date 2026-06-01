# Knowledge Base Skill

指导 agent 如何正确使用知识库 MCP 工具 (`save_solution`, `delete_solution`, `list_solutions`, `get_solution`, `search_solutions`)。

## 空知识库处理

当用户执行知识库查询操作（如"查一下数据库"、"搜索知识库"）时：

1. 调用 `list_solutions()`，检查返回结果
2. 如果结果中 **`kb_not_found` 为 `true`**：
   - 向用户输出：
     > 当前工作目录下未找到知识库，是否总结当前对话中已解决的问题，并新建知识库？
   - 如果用户同意：
     - 分析当前对话，提取已解决的问题及其解决方案（problem, cause, solution, tags, context, detail）
     - 调用 `question` 工具展示内容预览，提供 [确认存入 / 修改内容 / 取消] 三个选项
     - 用户确认后，调用 `save_solution` 写入
   - 如果用户拒绝：结束，不做任何操作
3. 如果结果中 `kb_not_found` 为 `false` 或不存在，但 `total == 0`：
   - 向用户输出："知识库为空，暂无记录。"
   - 可询问是否要存入当前对话中已解决的问题。

## 查询流程

| 用户说 | Agent 操作 |
|--------|-----------|
| "查看知识库" | 调用 `list_solutions()` → 展示编号列表 |
| "查看第 N 条详情" | 先调 `list_solutions()` 获取 ID → 调 `get_solution(id)` → 展示完整内容 |
| "搜索 XXX 的问题" | 调用 `search_solutions("XXX")` → 展示匹配结果及相似度 |
| "删除第 N 条" | 先调 `list_solutions()` 获取 ID → 调 `delete_solution(id)` → 确认结果 |

## 保存约束

- **保存前必须通过 `question` 工具让用户确认**，不得直接调用 `save_solution`
- **保存前不执行查重**，禁止调用 `search_solutions` 检查相似记录
- **禁止手写替代脚本**（如 `save_kb.py`），MCP 不可用时直接报告问题，不自行实现绕路方案
- `save_solution` 调用后仅写 `chroma_db/`，不在其他目录生成任何文件
