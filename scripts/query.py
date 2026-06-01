import os
import chromadb

from scripts.model import get_model


CHROMA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_db")


def get_collection():
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    return client.get_or_create_collection(
        name="solutions",
        metadata={"hnsw:space": "cosine"},
    )


def search_solutions(query: str, top_k: int = 5) -> list[dict]:
    model = get_model()
    query_embedding = model.encode(query).tolist()

    collection = get_collection()
    try:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=max(1, top_k),
            include=["metadatas", "distances"],
        )
    except Exception:
        return []

    if not results or not results.get("ids"):
        return []

    ids_list = results["ids"][0] if results.get("ids") and results["ids"][0] else []
    if not ids_list:
        return []

    metas = results.get("metadatas", [[]])[0] or []
    dists = results.get("distances", [[]])[0] or []

    output = []
    for i in range(len(ids_list)):
        meta = metas[i] if i < len(metas) else {}
        dist = dists[i] if i < len(dists) else 1.0
        similarity = max(0.0, 1 - dist)
        output.append({
            "id": ids_list[i],
            "problem": meta.get("problem", ""),
            "solution": meta.get("solution", ""),
            "tags": meta.get("tags", "").split(",") if meta.get("tags") else [],
            "context": meta.get("context", ""),
            "cause": meta.get("cause", ""),
            "detail": meta.get("detail", ""),
            "timestamp": meta.get("timestamp", ""),
            "similarity": f"{similarity:.1%}",
        })
    return output


def list_solutions(limit: int = 20, offset: int = 0) -> dict:
    collection = get_collection()
    total = collection.count()
    if total == 0:
        return {"total": 0, "records": []}

    results = collection.get(limit=limit, offset=offset, include=["metadatas"])
    records = []
    for i in range(len(results["ids"])):
        meta = results["metadatas"][i]
        records.append({
            "order": offset + i + 1,
            "id": results["ids"][i],
            "problem": meta.get("problem", ""),
        })
    return {"total": total, "records": records}


def get_solution(entry_id: str) -> dict | None:
    collection = get_collection()
    results = collection.get(ids=[entry_id], include=["metadatas", "documents"])
    if not results or not results.get("ids"):
        return None

    meta = results["metadatas"][0]
    return {
        "id": results["ids"][0],
        "problem": meta.get("problem", ""),
        "solution": meta.get("solution", ""),
        "tags": meta.get("tags", "").split(",") if meta.get("tags") else [],
        "context": meta.get("context", ""),
        "cause": meta.get("cause", ""),
        "detail": meta.get("detail", ""),
        "timestamp": meta.get("timestamp", ""),
    }
