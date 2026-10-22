import os
import sys
import types
from pathlib import Path

# Ensure rag-backend is on sys.path regardless of whether pytest is run
# from the repo root or inside the rag-backend directory.
backend_dir = str(Path(__file__).resolve().parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Stub the embeddings module so tests never load the real model.
fake = types.ModuleType("embeddings")
fake.embedder = None
sys.modules["embeddings"] = fake

# Provide a mock GROQ_API_KEY so importing modules that initialize Groq clients
# succeeds in test environments without requiring real credentials.
os.environ.setdefault("GROQ_API_KEY", "mock-groq-api-key")
