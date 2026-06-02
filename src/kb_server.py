import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server.fastmcp import FastMCP
from scripts.ingest import add_solution, delete_solution as del_solution
from scripts.query import search_solutions as query_search, list_solutions as query_list, get_solution as query_get

mcp = FastMCP("Knowledge Base")


@mcp.tool()
def save_solution(problem: str, solution: str, tags: list[str], context: str = "", cause: str = "", detail: str = "") -> str:
    """将问题解决方案保存到知识库中。
    调用前须通过 question 工具让用户确认内容，确认后方可写入。

    Args:
        problem: 问题的简短标题（如 "ZED 相机初始化失败，错误码 -1"）
        solution: 解决方案的详细步骤描述
        tags: 标签列表（如 ["zed", "camera", "硬件"]）
        context: 运行环境上下文（如 "Jetson Orin AGX, JetPack L4T r36.4.0"）
        cause: 问题产生的根本原因（如 "USB 供电不足导致 xda 守护进程无法枚举设备"）
        detail: 详细的错误现象、完整报错信息、重现步骤等补充说明
    """
    entry_id = add_solution(problem, solution, tags, context, cause, detail)
    return f"已保存到知识库 (ID: {entry_id})"


@mcp.tool()
def delete_solution(entry_id: str) -> str:
    """从知识库中删除一条记录。

    Args:
        entry_id: 要删除记录的 ID
    """
    del_solution(entry_id)
    return f"已删除 (ID: {entry_id})"


@mcp.tool()
def search_solutions(query: str, top_k: int = 5) -> list[dict]:
    """在知识库中搜索与问题描述最相似的解决方案。

    Args:
        query: 问题描述，将自动进行语义匹配
        top_k: 返回最相似的结果数量（默认 5）
    """
    return query_search(query, top_k)


@mcp.tool()
def list_solutions(limit: int = 20, offset: int = 0) -> dict:
    """查看知识库记录列表，按时间倒序返回。每条包含序号、问题摘要、标签和时间。

    Args:
        limit: 返回条数（默认 20）
        offset: 偏移量（默认 0）
    """
    return query_list(limit, offset)


@mcp.tool()
def get_solution(entry_id: str) -> dict | None:
    """查看某条记录的完整内容。

    Args:
        entry_id: 记录 ID
    """
    return query_get(entry_id)


if __name__ == "__main__":
    mcp.run(transport="stdio")
