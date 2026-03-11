# iOS Test Automator v2

Generate XCTest unit tests and XCUITest UI tests from natural language descriptions, powered by **Claude** (via LangChain) and a **RAG** pipeline built on your Swift source code.

---

## What It Does

1. **Ingests** your iOS Swift project into a Chroma vector store (screens, accessibility IDs, UI elements).
2. **Retrieves** relevant context at query time using semantic search (RAG).
3. **Generates** production-ready Swift test code via Claude, informed by the retrieved context.
4. **Validates** XCUITest contracts (app launch, explicit waits, assertions).
5. **Runs** tests via xcodebuild and optionally records video (macOS only, Streamlit UI).

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      Streamlit UI                        │
│  ui/app.py  — natural language input, test history,      │
│               xcodebuild runner, video recording          │
└───────────────────────┬─────────────────────────────────┘
                        │ HTTP (REST)
┌───────────────────────▼─────────────────────────────────┐
│                   FastAPI Backend                         │
│  backend/app/                                            │
│  ├── main.py          — lifespan, middleware, routers    │
│  ├── core/            — config (BaseSettings), prompts   │
│  ├── schemas/         — Pydantic request/response models │
│  ├── services/        — TestGenerator, RAGService        │
│  ├── api/routes/      — health, tests endpoints          │
│  └── utils/           — swift_utils, validators          │
└───────────────────────┬─────────────────────────────────┘
                        │ similarity_search
┌───────────────────────▼─────────────────────────────────┐
│                     RAG Module                            │
│  rag/                                                    │
│  ├── chunker.py  — Swift → Chunk (regex, brace-match)    │
│  ├── auditor.py  — heuristic accessibility audit         │
│  ├── store.py    — Chroma build/upsert, file iteration   │
│  └── cli.py      — ingest / query CLI commands           │
│                                                          │
│  Chroma vector store persisted to rag_store/             │
│  Embeddings: sentence-transformers/all-MiniLM-L6-v2      │
└─────────────────────────────────────────────────────────┘
```

---

## Setup

### 1. Install Dependencies

```bash
# Recommended: use a virtual environment
python -m venv .venv && source .venv/bin/activate

pip install -e .
# or directly:
pip install fastapi uvicorn pydantic pydantic-settings langchain langchain-anthropic \
            langchain-community chromadb sentence-transformers streamlit requests python-dotenv
```

### 2. Set Environment Variables

```bash
cp .env.example .env
# Edit .env — at minimum set ANTHROPIC_API_KEY and PROJECT_ROOT
```

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | _(required)_ | Your Anthropic API key |
| `ANTHROPIC_MODEL` | `claude-sonnet-4-5-20250929` | Claude model |
| `RAG_PERSIST_DIR` | `../rag_store` | Chroma DB path |
| `PROJECT_ROOT` | _(required for UI)_ | Path to iOS project root |

### 3. Ingest Your Swift Project

```bash
python -m rag.cli ingest \
  --app-dir /path/to/YourApp \
  --persist ./rag_store \
  --collection ios_app
```

Optional: fail early if accessibility IDs are missing:
```bash
python -m rag.cli ingest ... --fail-if-missing-ids
```

Smoke-test retrieval:
```bash
python -m rag.cli query \
  --persist ./rag_store \
  --collection ios_app \
  --q "login invalid password" \
  --k 8
```

### 4. Run the Backend

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### 5. Run the Streamlit UI

```bash
# Set PROJECT_ROOT env var or enter it in the sidebar
export PROJECT_ROOT=/path/to/iOS-test-automator
streamlit run ui/app.py
```

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Service info |
| `GET` | `/health` | Health check (LLM config status) |
| `POST` | `/generate-test` | Generate test from structured request |
| `POST` | `/generate-test-with-rag` | Generate test with RAG context auto-retrieval |
| `POST` | `/generate-tests-batch` | Generate multiple tests in parallel |

### Example: Generate with RAG

```bash
curl -X POST http://localhost:8000/generate-test-with-rag \
  -H "Content-Type: application/json" \
  -d '{
    "test_description": "Test login with invalid credentials and verify error message",
    "test_type": "ui"
  }'
```

---

## Project Structure

```
ios-test-automator-v2/
├── backend/app/
│   ├── main.py              # FastAPI app + lifespan
│   ├── core/config.py       # Pydantic BaseSettings
│   ├── core/prompts.py      # XCTest & XCUITest system prompts
│   ├── schemas/             # Request/response models
│   ├── services/            # TestGenerator, RAGService
│   ├── api/routes/          # health.py, tests.py
│   └── utils/               # swift_utils, validators
├── rag/
│   ├── chunker.py           # Swift → Chunks
│   ├── auditor.py           # Accessibility audit
│   ├── store.py             # Chroma helpers
│   └── cli.py               # ingest / query CLI
├── ui/app.py                # Streamlit frontend
├── ios-app/                 # Sample iOS app (Swift)
├── pyproject.toml
└── .env.example
```

---

## Notes

- RAG parsing uses regex + brace-matching (MVP). For production accuracy, replace with SwiftSyntax.
- The Streamlit runner (`xcodebuild`, video recording) requires macOS with Xcode installed.
- The backend and RAG module work cross-platform.
