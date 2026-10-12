from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from indexer import get_or_build_index
from retrieval import retrieve
from llm import call_groq_with_retry
from prompts import build_prompt
from schemas import IndexRequest, ChatRequest

app = FastAPI()

# Chrome extensions call from "chrome-extension://<id>" origin — allow that
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this to your extension's exact origin once you have the ID
    allow_methods=["*"],
    allow_headers=["*"],
)

chat_sessions = {}


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
    history = chat_sessions.get(req.video_id, [])
    prompt = build_prompt(retrieved, history, req.query)

    answer = call_groq_with_retry(prompt)
    history.append({"role": "user", "content": req.query})
    history.append({"role": "assistant", "content": answer})
    chat_sessions[req.video_id] = history

    return {"success": True, "answer": answer}


@app.get("/health")
def health():
    return {"status": "ok"}