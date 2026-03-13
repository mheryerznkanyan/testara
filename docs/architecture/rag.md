# RAG Pipeline

Deep dive into Testara's Retrieval-Augmented Generation pipeline.

## Overview

The RAG pipeline enables code-aware test generation by:

1. **Ingesting** your Swift codebase
2. **Chunking** code into semantic units
3. **Embedding** chunks for semantic search
4. **Retrieving** relevant context for each test
5. **Augmenting** LLM prompts with code context

*Full documentation coming soon.*

## Components

- **Ingestion:** Code scanning and parsing
- **Chunker:** AST-based code splitting
- **Embeddings:** Sentence transformers
- **Vector Store:** Chroma DB
- **Retrieval:** Semantic search

See [Architecture Overview](overview.md) for more details.
