# Content Intelligence Hub - macOS App

## What This Is

A native-feeling macOS desktop app for marketing content intelligence. Electron + React frontend with a Python FastAPI sidecar backend. Local-first: SQLite + sqlite-vss for storage, local sentence-transformers for embeddings, Anthropic API for LLM.

## Architecture

- **Electron** main process manages window + spawns Python sidecar
- **React + TypeScript** frontend with TailwindCSS + shadcn/ui
- **Python FastAPI** sidecar on localhost:8420
- **SQLite + sqlite-vss** for content storage and vector search
- **sentence-transformers** (all-MiniLM-L6-v2, ONNX) for local embeddings
- **Anthropic Claude API** for LLM features (provider-abstracted for future local LLM support)

## Key Design Docs

- `docs/plans/2026-03-06-macos-app-design.md` — full architecture design

## Prior Art

This app is a desktop rebuild of a Streamlit web app (see `/Users/jm/Projects/Content-Intelligence-Hub-Demo/`). Port agent logic and search functions from that codebase's `src/` directory.

## Dev Workflow

```bash
# Terminal 1: Python sidecar
cd sidecar && python -m uvicorn api:app --port 8420 --reload

# Terminal 2: Electron + React dev
npm run dev
```

## Tech Stack

- **Frontend**: Electron, React, TypeScript, TailwindCSS, shadcn/ui, @tanstack/react-table
- **Backend**: Python 3.12+, FastAPI, LangGraph, Anthropic SDK, sentence-transformers, sqlite-vss
- **Packaging**: electron-builder, PyInstaller/python-build-standalone
- **Testing**: Vitest (frontend), pytest (sidecar)

## Conventions

- TypeScript strict mode
- Python: type hints, pytest, ruff
- Prefer editing existing files over creating new ones
- Small, focused, atomic commits
