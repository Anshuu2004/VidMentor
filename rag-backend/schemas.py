from pydantic import BaseModel


class IndexRequest(BaseModel):
    video_id: str


class ChatRequest(BaseModel):
    video_id: str
    query: str
    current_time: float | None = None