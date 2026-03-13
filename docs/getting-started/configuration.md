# Configuration

Configure Testara for your iOS project.

## Environment Variables

All configuration is done via the `.env` file in the project root.

### Required Settings

```bash
# Anthropic API Configuration
ANTHROPIC_API_KEY=your_key_here          # Your Claude API key
ANTHROPIC_MODEL=claude-sonnet-4          # Model to use

# iOS Project
PROJECT_ROOT=/path/to/your/ios/app       # Absolute path to your iOS app
```

### Optional Settings

```bash
# LLM Configuration
LLM_TEMPERATURE=0.3                      # Model temperature (0.0-1.0)
LLM_MAX_TOKENS=4096                     # Max tokens per request

# RAG Configuration
RAG_PERSIST_DIR=../rag_store            # Vector store location
RAG_COLLECTION=ios_app                  # Collection name
RAG_EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2  # Embedding model
RAG_TOP_K=10                            # Number of relevant chunks to retrieve

# Server Configuration
PORT=8000                               # Backend port
HOST=0.0.0.0                           # Backend host
```

## First-Time Setup

### Automatic Setup (Recommended)

Running `./start.sh` automatically:

1. Creates `LLMGeneratedTest.swift` in your UI test target
2. Adds it to your Xcode project (using `pbxproj`)
3. Configures file references

### Manual Setup

If automatic setup fails:

1. **Create test file:**
   ```bash
   touch YourAppUITests/LLMGeneratedTest.swift
   ```

2. **Add to Xcode:**
    - Right-click your UI test target in Xcode
    - Select "Add Files to..."
    - Choose `LLMGeneratedTest.swift`
    - ✅ Ensure your UI test target is checked

3. **Verify:**
    - File appears in Project Navigator
    - File is included in UI test target membership

## RAG Indexing

Your iOS app is automatically indexed on first run. 

### Re-index After Code Changes

```bash
python -m rag.cli ingest --app-dir "$PROJECT_ROOT" --persist ./rag_store
```

### What Gets Indexed

- ✅ Swift source files (`.swift`)
- ✅ SwiftUI views
- ✅ UIKit ViewControllers
- ✅ Accessibility identifiers
- ✅ Navigation patterns
- ✅ Storyboard/XIB files

### What's Excluded

- ❌ Build artifacts
- ❌ Dependencies (`Pods/`, `Carthage/`)
- ❌ `.build/` directories
- ❌ Test files (unless explicitly included)

## Model Selection

Testara supports multiple Claude models:

| Model | Best For | Speed | Quality |
|-------|----------|-------|---------|
| `claude-sonnet-4` | Production use | Fast | High |
| `claude-opus-4` | Complex tests | Slow | Highest |
| `claude-haiku-3.5` | Simple tests | Fastest | Good |

Set via `ANTHROPIC_MODEL` in `.env`.

## Advanced Configuration

### Custom Embedding Model

To use a different embedding model:

```bash
RAG_EMBED_MODEL=sentence-transformers/all-mpnet-base-v2
```

Popular options:
- `all-MiniLM-L6-v2` (default, fast)
- `all-mpnet-base-v2` (slower, better quality)
- `multi-qa-MiniLM-L6-cos-v1` (optimized for Q&A)

### Custom Vector Store Location

```bash
RAG_PERSIST_DIR=/custom/path/to/vectorstore
```

!!! warning "Disk Space"
    Vector store size depends on codebase size. Allow ~50-100MB per 10k lines of code.

## Next Steps

- [Learn how to generate tests](../usage/generating-tests.md)
- [Understand the RAG pipeline](../architecture/rag.md)
