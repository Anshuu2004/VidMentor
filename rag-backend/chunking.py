from config import WINDOW_SEC

   # Fixed time-window chunking: segments are grouped into windows of about
   # WINDOW_SEC seconds, each chunk tagged with its start/end timestamp.
def chunk_transcript(transcript, window_sec=WINDOW_SEC):
    if not transcript:
        return []
    chunks = []
    current_text, current_start = [], transcript[0]['start']
    for seg in transcript:
        if seg['start'] - current_start > window_sec and current_text:
            chunks.append({"text": " ".join(current_text), "start": current_start, "end": seg['start']})
            current_text, current_start = [], seg['start']
        current_text.append(seg['text'])
    if current_text:
        chunks.append({"text": " ".join(current_text), "start": current_start, "end": transcript[-1]['start']})
    return chunks