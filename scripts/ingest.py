import os
import uuid
from datetime import datetime, timezone

import chromadb

from scripts.model import get_model


CHROMA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_db")


def get_collection():
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    return client.get_or_create_collection(
        name="solutions",
        metadata={"hnsw:space": "cosine"},
    )


def add_solution(problem: str, solution: str, tags: list[str], context: str = "", cause: str = "", detail: str = "") -> str:
    entry_id = str(uuid.uuid4())
    document = f"问题：{problem}\n原因：{cause}\n方案：{solution}\n环境：{context}"
    if detail:
        document += f"\n详情：{detail}"
    model = get_model()
    embedding = model.encode(document).tolist()

    metadata = {
        "problem": problem,
        "solution": solution,
        "tags": ",".join(tags),
        "context": context,
        "cause": cause,
        "detail": detail,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    collection = get_collection()
    collection.add(
        embeddings=[embedding],
        documents=[document],
        metadatas=[metadata],
        ids=[entry_id],
    )
    return entry_id
