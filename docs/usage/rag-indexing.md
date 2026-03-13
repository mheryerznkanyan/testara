# RAG Indexing

How Testara indexes and understands your codebase.

## What is RAG?

Retrieval-Augmented Generation (RAG) allows Testara to:

- Read and understand your Swift code
- Find relevant code sections for each test
- Generate accurate element queries
- Avoid hallucinated selectors

## Initial Indexing

Your app is automatically indexed on first run.

## Manual Re-indexing

After code changes:

```bash
python -m rag.cli ingest --app-dir "$PROJECT_ROOT" --persist ./rag_store
```

## What Gets Indexed

- Swift source files
- SwiftUI views
- UIKit ViewControllers  
- Accessibility identifiers
- Storyboard/XIB files

*Full guide coming soon.*
