import faiss
from embeddings import embedder
from chunking import chunk_transcript
from transcript import get_transcript
from cache import video_cache, save_to_disk, load_from_disk

def build_index_for_video(video_id):
    transcript, error = get_transcript(video_id)
    if transcript is None:
        return None, error
    chunks = chunk_transcript(transcript)
    embeddings = embedder.encode([c["text"] for c in chunks], convert_to_numpy=True, normalize_embeddings=True)
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)
    return (chunks, index), None



def get_or_build_index(video_id):
    if video_id in video_cache:
        return video_cache[video_id], None
    disk_result = load_from_disk(video_id)
    if disk_result:
        video_cache[video_id] = disk_result
        return disk_result, None
    result, error = build_index_for_video(video_id)
    if result is None:
        return None, error
    chunks, index = result
    save_to_disk(video_id, chunks, index)
    video_cache[video_id] = (chunks, index)
    return (chunks, index), None
