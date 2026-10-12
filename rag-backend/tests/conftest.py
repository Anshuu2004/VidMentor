import sys
import types

# Stub the embeddings module so tests never load the real model.
fake = types.ModuleType("embeddings")
fake.embedder = None
sys.modules["embeddings"] = fake