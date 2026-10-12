from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import HISTORY_MESSAGES
from indexer import get_or_build_index
from retrieval import retrieve
from llm import call_groq_with_retry

app = FastAPI()

# Chrome extensions call from "chrome-extension://<id>" origin — allow that
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this to your extension's exact origin once you have the ID
    allow_methods=["*"],
    allow_headers=["*"],
)

chat_sessions = {}


# ---------- API models ----------
class IndexRequest(BaseModel):
    video_id: str


class ChatRequest(BaseModel):
    video_id: str
    query: str
    current_time: float | None = None


# ---------- Endpoints ----------
@app.post("/index")
def index_video(req: IndexRequest):
    result, error = get_or_build_index(req.video_id)
    if result is None:
        return {"success": False, "error": error}
    return {"success": True, "message": "Video indexed and ready."}


@app.post("/chat")
def chat(req: ChatRequest):
    result, error = get_or_build_index(req.video_id)
    if result is None:
        return {"success": False, "error": error}
    chunks, index = result

    retrieved = retrieve(req.query, chunks, index, req.current_time)
    context = "\n\n".join(
        f"[{int(c['start']//60)}:{int(c['start']%60):02d}] {c['text']}" for c in retrieved
    )
    history = chat_sessions.get(req.video_id, [])
    history_text = "\n".join(f"{h['role']}: {h['content']}" for h in history[-HISTORY_MESSAGES:]) or "(no previous messages)"

    prompt = f"""You're helping a student who's stuck on a concept while watching a YouTube video.
Use ONLY the transcript context below to answer. If it's not covered, say so honestly.
If the question refers to earlier conversation (like "it"/"that"), use the history to resolve it.

Transcript context:
{context}

Conversation so far:
{history_text}

Student's new question: {req.query}

Answer clearly and concisely, referencing the timestamp if helpful:"""

    answer = call_groq_with_retry(prompt)
    history.append({"role": "user", "content": req.query})
    history.append({"role": "assistant", "content": answer})
    chat_sessions[req.video_id] = history

    return {"success": True, "answer": answer}


@app.get("/health")
def health():
    return {"status": "ok"}