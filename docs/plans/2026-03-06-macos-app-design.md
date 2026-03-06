# Content Intelligence Hub - macOS App Design

**Date:** 2026-03-06
**Status:** Approved

## Goal

Turn the Content Intelligence Hub from a Streamlit web app into a native-feeling macOS desktop application. Fully local-first: bundled database, local embeddings, local file ingestion. Only external dependency is the Anthropic API for LLM features.

## Architecture

Electron app (TypeScript/React frontend) + Python sidecar (FastAPI backend).

```
+---------------------------------------------+
|  Electron App                                |
|  +---------------------------------------+   |
|  |  React Frontend (TypeScript)          |   |
|  |  - Dashboard, Library, Detail views   |   |
|  |  - TailwindCSS + shadcn/ui           |   |
|  +----------------+----------------------+   |
|                   | HTTP (localhost:8420)     |
|  +----------------+----------------------+   |
|  |  Python Sidecar (FastAPI)             |   |
|  |  - LangGraph agents (query, repurpose)|   |
|  |  - Embedding (sentence-transformers)  |   |
|  |  - SQLite + sqlite-vss               |   |
|  |  - File watcher / importer            |   |
|  |  - LLM provider abstraction           |   |
|  +---------------------------------------+   |
+---------------------------------------------+
```

- Electron main process spawns the Python sidecar on startup
- React renderer communicates with sidecar via REST on localhost
- App data in `~/Library/Application Support/ContentIntelligenceHub/`

## Bundled Infrastructure

| Component | Implementation | Size |
|-----------|---------------|------|
| Python runtime | python-build-standalone or PyInstaller | ~40MB |
| Database | SQLite + sqlite-vss (vector search) | ~2MB |
| Embedding model | all-MiniLM-L6-v2 (ONNX) | ~25MB |
| Python deps | FastAPI, LangGraph, Anthropic SDK, etc. | ~30MB |

Total app: ~150-200MB. No external dependencies for the user.

## Content Ingestion

- User configures watched folders in Settings
- File watcher (Python watchdog) monitors for new/changed/deleted files
- Supported formats: markdown, PDF (pymupdf), Word (python-docx), plain text
- On detection: extract text, generate embedding locally, insert into SQLite
- Metadata (content_type, persona, etc.) can be auto-inferred by LLM or manually tagged

### Source Abstraction

`ContentSource` interface with `LocalFileSource` implementation. Future sources (Google Drive, Notion, etc.) implement the same interface.

## LLM Provider Abstraction

`LLMProvider` base class with `AnthropicProvider` implementation. User provides API key in Settings. Architecture supports adding local LLM (Ollama) or other providers later.

## Frontend

React + TypeScript + TailwindCSS + shadcn/ui. Same views as current app:

- **Dashboard** -- search bar, recent content cards
- **Library - Existing** -- table (@tanstack/react-table), filter bar, preview panel
- **Library - Generated** -- same pattern, format/tone filters
- **Content Detail** -- full content view with repurpose panel and save
- **Settings** -- API key, watched folders, theme (light/dark)

UX upgrades over Streamlit:
- No page reruns -- instant filter/selection updates
- Keyboard shortcuts (Cmd+K search, arrow keys for table nav)
- Native window controls, menu bar, dock icon
- Drag & drop files to import

## Project Structure

```
content-intelligence-hub/
+-- electron/
|   +-- main.ts              # Electron main process, spawns sidecar
|   +-- preload.ts           # IPC bridge
|   +-- sidecar.ts           # Python process manager
+-- src/                     # React frontend
|   +-- components/
|   +-- views/
|   +-- api/                 # HTTP client to sidecar
|   +-- App.tsx
+-- sidecar/                 # Python backend (FastAPI)
|   +-- api.py               # REST endpoints
|   +-- agents/              # LangGraph agents (ported from current)
|   +-- search.py            # SQLite search (ported)
|   +-- generated.py         # Generated content queries (ported)
|   +-- embeddings.py        # Local sentence-transformers
|   +-- db.py                # SQLite + sqlite-vss connection
|   +-- ingest.py            # File watcher + text extraction
|   +-- providers/           # LLM provider abstraction
|   |   +-- base.py
|   |   +-- anthropic.py
|   +-- sources/             # Content source abstraction
|       +-- base.py
|       +-- local_files.py
+-- package.json
+-- electron-builder.yml     # Packaging config
+-- pyproject.toml           # Python sidecar deps
```

## Distribution

### Development (no signing needed)

```bash
# Terminal 1: Python sidecar
cd sidecar && python -m uvicorn api:app --port 8420

# Terminal 2: Electron dev mode
npm run dev
```

Run unsigned locally for development and testing. No Apple Developer account needed.

### Production Distribution

1. **Apple Developer Account** -- $99/year, required for distribution
2. **Code signing** -- Developer ID Application certificate from Apple
3. **Notarization** -- `xcrun notarytool submit` so Gatekeeper allows the app
4. **Packaging** -- electron-builder produces signed `.dmg`
5. **Auto-updates** -- electron-updater checks GitHub Releases
6. **Optional**: Homebrew Cask formula for `brew install --cask content-intelligence-hub`

### Distribution Steps (detailed)

1. Enroll in Apple Developer Program ($99/year) at developer.apple.com
2. Create a "Developer ID Application" certificate in Xcode > Settings > Accounts
3. Configure electron-builder.yml with signing identity and notarization credentials
4. Build: `npm run dist` (builds .app, signs, notarizes, creates .dmg)
5. Upload .dmg to GitHub Releases (or your own hosting)
6. electron-updater checks for new releases on app startup

## Key Decisions

- **Electron** over SwiftUI/Tauri -- proven path (Claude Desktop, Cursor, ChatGPT), web tech, cross-platform potential
- **Python sidecar** over full TS rewrite -- reuse existing agent/search code
- **SQLite + sqlite-vss** over PostgreSQL -- fully local, no install, bundled
- **Local embeddings** (sentence-transformers) over Voyage API -- works offline, no API cost
- **Anthropic API** for LLM -- high quality, with provider abstraction for future local LLM support
- **Local file source** with abstraction -- Google Drive etc. can be added later
