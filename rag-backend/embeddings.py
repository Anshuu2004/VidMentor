from sentence_transformers import SentenceTransformer
from config import EMBEDDING_MODEL

# Loaded once at import time and shared by indexing and retrieval.
embedder = SentenceTransformer(EMBEDDING_MODEL)

def get_embedder(model_name: str | None = None) -> SentenceTransformer:
    if model_name is None or model_name == EMBEDDING_MODEL:
        return embedder
    return SentenceTransformer(model_name)