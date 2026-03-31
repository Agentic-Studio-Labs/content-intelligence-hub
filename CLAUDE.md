# Marketing RAG Assistant

Public portfolio name for this codebase: **local-first RAG over a curated content library** (Electron + React + FastAPI).  
Repository: [Agentic-Studio-Labs/marketing-rag-assistant](https://github.com/Agentic-Studio-Labs/marketing-rag-assistant).

## What “marketing” means here

The **RAG stack is domain-agnostic** (ingest → chunk → embed → sqlite-vss → retrieve → LLM). The marketing angle is mostly:

- **Data shape** — content types, persona, funnel stage, performance metadata on chunks.
- **Prompts / agents** — tuned for “content discovery” rather than e.g. financial coaching.

Swap corpus + filters + prompts and the same architecture applies to books, wikis, or support docs.

## What this is

A native-feeling macOS desktop app. Electron + React frontend with a Python FastAPI sidecar. Local-first: SQLite + **sqlite-vss** for vector search, local **sentence-transformers** for embeddings, **Anthropic** (or another provider via the abstraction) for the LLM.

## Architecture

- **Electron** — window + spawns Python sidecar
- **React + TypeScript** — TailwindCSS + shadcn/ui
- **FastAPI** sidecar — default `localhost:8420`
- **SQLite + sqlite-vss** — storage + similarity search over embeddings
- **sentence-transformers** (e.g. all-MiniLM-L6-v2, ONNX) — local embeddings
- **LLM** — provider interface; Anthropic in current wiring

## sqlite-vss (quick)

SQLite extension for **nearest-neighbor search on embedding vectors** — semantic retrieval in one database file without a separate vector DB.

## Dev workflow

```bash
# Terminal 1: Python sidecar
cd sidecar && python -m uvicorn api:app --port 8420 --reload

# Terminal 2: Electron + React dev
npm run dev
```

## Chatbot-style UI

The core API is single-turn Q&A (query → RAG → answer). A **chat UI** fits naturally: each user message runs the same retrieval pipeline; add **recent messages or a short summary** to the LLM prompt for multi-turn coherence; optional **thread store** in SQLite for durable memory.

## Portfolio / publishing notes

- **First push to GitHub** — if you see `GH007` / email privacy errors, fix under GitHub **Settings → Emails** (allow the push or use your `users.noreply.github.com` address in `git config user.email`).

## Tech stack

- **Frontend**: Electron, React, TypeScript, TailwindCSS, shadcn/ui, @tanstack/react-table
- **Backend**: Python 3.12+, FastAPI, LangGraph (agents), sentence-transformers, sqlite-vss
- **Testing**: Vitest (frontend), pytest (sidecar)

## Conventions

- TypeScript strict mode
- Python: type hints, pytest, ruff
- Prefer small, focused commits


