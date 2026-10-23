import os
import sys
import types

# Stub the embeddings module so tests never load the real model.
fake = types.ModuleType("embeddings")
fake.embedder = None
sys.modules["embeddings"] = fake

# Provide a mock GROQ_API_KEY so importing modules that initialize Groq clients
# succeeds in test environments without requiring real credentials.
os.environ.setdefault("GROQ_API_KEY", "mock-groq-api-key")
