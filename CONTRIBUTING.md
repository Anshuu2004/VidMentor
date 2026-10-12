# Contributing to VidMentor

Thanks for helping! VidMentor is a Chrome extension plus a FastAPI backend
that answers questions about a YouTube video using its transcript (RAG).

## Quick start

1. Fork the repo and clone your fork.
2. Backend setup (see the README for details):
```
   cd rag-backend
   python -m venv venv
   pip install -r requirements.txt -r requirements-dev.txt
   cp .env.example .env      # then add your free Groq key
   uvicorn main:app --reload --port 8000
```
3. Load the extension: `chrome://extensions` -> Developer mode -> Load unpacked
   -> select `yt-doubt-extension`.
4. For local development, set `BACKEND_URL` in `background.js` to
   `http://localhost:8000`. **Do not commit this change.**

## Picking an issue

- Look for `good first issue`, `intermediate`, or `advanced` labels.
- Comment on the issue to be assigned before you start, so two people
  don't build the same thing.
- Not sure about scope? Ask in the issue first.

## Making a change

1. Create a branch from `main`: `git checkout -b feat/short-description`
2. Keep the PR small and focused on one issue.
3. Run the tests: `cd rag-backend && python -m pytest`
4. Add or update tests when you change behavior in `chunking.py`,
   `retrieval.py`, `prompts.py`, or `indexer.py`.
5. Open a pull request and link the issue (`Closes #12`).

## Where things live

| To change...            | Edit                  |
|-------------------------|-----------------------|
| window size, top-k, models | `config.py`        |
| how transcripts are split  | `chunking.py`      |
| ranking / time penalty     | `retrieval.py`     |
| the LLM prompt             | `prompts.py`       |
| API routes                 | `main.py`          |
| chat widget UI             | `content.js`, `content.css` |

## Commit messages

Use a short prefix: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`.

## Please don't

- Commit `.env`, API keys, `venv/`, or `rag_cache/`.
- Commit a `BACKEND_URL` pointing at localhost.
- Mix unrelated changes in one PR.

## Reviews

I aim to review pull requests within a few days. Be kind, and ask
questions freely. Everyone here is learning.