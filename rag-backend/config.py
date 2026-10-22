import os
from dotenv import load_dotenv

load_dotenv()

# Secrets (from .env, never hardcode)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Models
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
LLM_MODEL = "openai/gpt-oss-20b"
LLM_TEMPERATURE = 0.3

# Transcript
PREFERRED_LANGS = ("en", "hi")

# Chunking
WINDOW_SEC = 40

# Retrieval
TOP_K = 4
TIME_WINDOW_SEC = 180
TIME_PENALTY_PER_SEC = 0.001

# LLM calls and chat history
MAX_RETRIES = 3
HISTORY_MESSAGES = 6

# Cache
CACHE_DIR = "rag_cache"