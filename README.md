# Testara

**AI-powered iOS test automation** — Generate and execute XCTest UI tests from natural language descriptions.

---

## 🚀 Quick Start

```bash
# 1. Clone
git clone https://github.com/mheryerznkanyan/testara.git
cd testara

# 2. Run setup
./setup.sh

# 3. Start backend
cd backend
uvicorn app.main:app --reload --port 8000

# 4. Start frontend (optional)
cd ../frontend
npm install && npm run dev
```

**Open:** http://localhost:3000

---

## ✨ Features

- ✅ **AI test generation** — Natural language → XCTest code
- ✅ **RAG-powered** — Analyzes your iOS codebase automatically
- ✅ **Smart context** — Extracts screens, navigation, accessibility IDs
- ✅ **Test execution** — Runs tests on iOS Simulator
- ✅ **Docker support** — One-command deployment

---

## 📋 Requirements

- **macOS** (for iOS Simulator and Xcode)
- **Python 3.11+**
- **Node.js 18+** (for frontend)
- **Xcode** with Command Line Tools
- **Anthropic API key** (for Claude)

---

## 🔧 Detailed Setup

### Step 1: Clone Repository

```bash
git clone https://github.com/mheryerznkanyan/testara.git
cd testara
```

### Step 2: Install Python Dependencies

```bash
# Create virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate

# Install packages
pip install -r backend/requirements.txt
```

### Step 3: Configure Environment

```bash
# Copy example config
cp .env.example .env

# Edit .env and set:
# - ANTHROPIC_API_KEY (required)
# - PROJECT_ROOT (path to your iOS app)
# - XCODE_PROJECT (path to .xcodeproj)
# - XCODE_SCHEME (your scheme name)
```

**Required settings:**
```bash
ANTHROPIC_API_KEY=your_key_here
PROJECT_ROOT=/path/to/your/ios/app
XCODE_PROJECT=/path/to/YourApp.xcodeproj
XCODE_SCHEME=YourApp
```

### Step 4: Index Your iOS App

```bash
# Index your Swift codebase
python3 -m rag.cli ingest \
  --app-dir /path/to/your/ios/app \
  --persist ./rag_store \
  --collection ios_app

# Generate app context
python3 generate_app_context.py
```

### Step 5: Start Backend

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

Backend will be available at: http://localhost:8000

### Step 6: Start Frontend (Optional)

```bash
cd frontend
npm install
npm run dev
```

Frontend will be available at: http://localhost:3000

---

## 🎯 How It Works

```
Your iOS App Code
      ↓
   RAG Indexing
   (AST parsing, semantic analysis)
      ↓
   App Context Extraction
   (screens, navigation, accessibility IDs)
      ↓
   AI Enrichment
   (brief description → detailed test spec)
      ↓
   Test Generation
   (Claude generates XCTest code)
      ↓
   Test Execution
   (runs on iOS Simulator)
      ↓
   Generated UI Test + Video Recording
```

---

## 💡 Usage

### Generate Test via API

```bash
curl -X POST http://localhost:8000/generate-test-with-rag \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Test login with valid credentials"
  }'
```

### Generate Test via Frontend

1. Open http://localhost:3000
2. Enter test description: "Test login with valid credentials"
3. Click "Generate Test"
4. Copy generated XCTest code
5. Add to your Xcode project

### Execute Test

The generated test can be run directly in Xcode or via command line:

```bash
cd /path/to/your/ios/app
xcodebuild test \
  -scheme YourApp \
  -destination 'platform=iOS Simulator,name=iPhone 16' \
  -only-testing:YourAppUITests/GeneratedTests
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│ Next.js Frontend (Optional)                             │
│ frontend/ — React UI for test generation                │
└───────────────────────┬─────────────────────────────────┘
                        │ HTTP REST API
┌───────────────────────▼─────────────────────────────────┐
│ FastAPI Backend                                          │
│ backend/app/                                             │
│ ├── main.py — API server                                │
│ ├── services/                                            │
│ │   ├── test_generator.py — AI test generation          │
│ │   ├── enrichment_service.py — Description enhancement │
│ │   ├── navigation_service.py — Screen detection        │
│ │   └── rag_service.py — Vector store queries           │
│ └── api/routes/tests.py — Test generation endpoints     │
└───────────────────────┬─────────────────────────────────┘
                        │ Semantic search
┌───────────────────────▼─────────────────────────────────┐
│ RAG Module                                               │
│ rag/                                                     │
│ ├── chunker.py — Swift code → semantic chunks           │
│ ├── auditor.py — Accessibility analysis                 │
│ ├── store.py — Chroma vector store management           │
│ └── cli.py — Indexing commands                          │
│                                                          │
│ Chroma vector store (./rag_store/)                      │
│ Embeddings: sentence-transformers/all-MiniLM-L6-v2      │
└──────────────────────────────────────────────────────────┘
```

---

## 🐳 Docker Deployment

```bash
# Start all services
docker-compose up -d

# Backend: http://localhost:8000
# Frontend: http://localhost:3000
```

**First time setup:**
```bash
# Index your app inside the container
docker-compose exec backend python -m rag.cli ingest \
  --app-dir /app/ios-app \
  --persist /app/rag_store
```

---

## 📚 Documentation

- **[Setup Guide](DEPLOYMENT.md)** — Detailed installation
- **[Settings Guide](SETTINGS-GUIDE.md)** — Configuration options
- **[Test Execution](TEST-EXECUTION-GUIDE.md)** — Running generated tests
- **[Contributing](CONTRIBUTING.md)** — How to contribute

---

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🔗 Links

- **Repository:** https://github.com/mheryerznkanyan/testara
- **Issues:** https://github.com/mheryerznkanyan/testara/issues
- **Website:** https://testara.dev _(coming soon)_

---

## 💡 Built With

- **[LangChain](https://python.langchain.com/)** — AI orchestration
- **[Claude (Anthropic)](https://www.anthropic.com/)** — Test generation
- **[Chroma](https://www.trychroma.com/)** — Vector database
- **[FastAPI](https://fastapi.tiangolo.com/)** — Backend API
- **[Next.js](https://nextjs.org/)** — Frontend UI
- **[Docker](https://www.docker.com/)** — Containerization

---

Made with ⚡ by [Mher Yerznkanyan](https://github.com/mheryerznkanyan)
