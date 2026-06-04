import os
from pathlib import Path

MODEL_NAME = "all-MiniLM-L6-v2"
_HF_CACHE = Path(os.path.expanduser("~")) / ".cache" / "huggingface" / "hub"

_model = None

def is_model_cached() -> bool:
    model_dir = _HF_CACHE / f"models--sentence-transformers--{MODEL_NAME}"
    if not model_dir.exists():
        return False
    snapshots_dir = model_dir / "snapshots"
    if not snapshots_dir.exists():
        return False
    for snapshot in snapshots_dir.iterdir():
        if not snapshot.is_dir():
            continue
        if (snapshot / "model.safetensors").exists():
            return True
    return False

def get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(MODEL_NAME)
    return _model
