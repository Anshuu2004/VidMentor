from sentence_transformers import SentenceTransformer
from config import EMBEDDING_MODEL

# Loaded once at import time and shared by indexing and retrieval.
embedder = SentenceTransformer(EMBEDDING_MODEL)