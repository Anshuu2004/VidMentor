import os
import pickle
import faiss
from config import CACHE_DIR

os.makedirs(CACHE_DIR, exist_ok=True)

# In-memory cache: video_id -> (chunks, index)
video_cache = {}

def save_to_disk(video_id, chunks, index):
    faiss.write_index(index, f"{CACHE_DIR}/{video_id}.index")
    with open(f"{CACHE_DIR}/{video_id}_chunks.pkl", "wb") as f:
        pickle.dump(chunks, f)

def load_from_disk(video_id):
    idx_path, chunks_path = f"{CACHE_DIR}/{video_id}.index", f"{CACHE_DIR}/{video_id}_chunks.pkl"
    if os.path.exists(idx_path) and os.path.exists(chunks_path):
        with open(chunks_path, "rb") as f:
            chunks = pickle.load(f)
        return chunks, faiss.read_index(idx_path)
    return None