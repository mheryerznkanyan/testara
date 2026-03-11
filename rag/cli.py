"""
rag/cli.py

Command-line interface for the iOS RAG pipeline.

Usage:
  # Ingest a Swift project:
  python -m rag.cli ingest --app-dir /path/to/ios --persist ./rag_store --collection ios_app

  # Query (smoke test):
  python -m rag.cli query --persist ./rag_store --collection ios_app --q "login invalid password" --k 8
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

from langchain_core.documents import Document

from rag.chunker import build_chunks_for_file, Chunk
from rag.auditor import audit_accessibility
from rag.store import (
    build_vectorstore,
    upsert_documents,
    prune_stale_documents,
    iter_swift_files,
    normalize_path,
    read_text,
    safe_json,
)

DEFAULT_EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def _generate_app_context(persist_dir: str, collection: str, embed_model: str):
    """Generate APP_CONTEXT.md after indexing"""
    # Import here to avoid circular dependencies
    import sys
    from pathlib import Path
    
    # Add backend to path if not already there
    backend_path = Path(__file__).parent.parent / "backend"
    if str(backend_path) not in sys.path:
        sys.path.insert(0, str(backend_path))
    
    from app.core.config import settings
    from app.services.rag_service import RAGService
    from app.services.context_extractor import AppContextExtractor
    
    # Create RAG service pointing to this index
    rag_service = RAGService(settings=settings)
    extractor = AppContextExtractor(rag_service)
    
    # Generate and save
    output_path = Path(persist_dir) / "APP_CONTEXT.md"
    extractor.save_to_file(str(output_path))


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_ingest(args: argparse.Namespace) -> int:
    app_dir = Path(args.app_dir).expanduser().resolve()
    if not app_dir.exists() or not app_dir.is_dir():
        print(f"ERROR: app-dir not found or not a directory: {app_dir}", file=sys.stderr)
        return 2

    all_chunks: List[Chunk] = []
    swift_files = list(iter_swift_files(app_dir))
    if not swift_files:
        print("ERROR: no .swift files found under app-dir", file=sys.stderr)
        return 2

    for p in swift_files:
        rel = normalize_path(p, app_dir)
        text = read_text(p)
        if not text.strip():
            continue
        all_chunks.extend(build_chunks_for_file(text, rel))

    findings, summary = audit_accessibility(all_chunks)

    audit_doc = Document(
        page_content=safe_json({
            "type": "ACCESSIBILITY_AUDIT",
            "summary": summary,
            "flagged": [f.__dict__ for f in findings[:200]],
            "total_flagged": len(findings),
        }),
        metadata={"kind": "accessibility_audit", "path": "_audit_"},
    )

    if args.fail_if_missing_ids and len(findings) > 0:
        print("ACCESSIBILITY AUDIT FAILED (missing IDs detected).")
        print(safe_json({
            "flagged_screens": len(findings),
            "examples": [f.__dict__ for f in findings[:20]],
            "action": (
                "Add .accessibilityIdentifier(...) to interactive elements "
                "on these screens before generating UI tests."
            ),
        }))
        return 3

    docs: List[Document] = [audit_doc]
    for ch in all_chunks:
        docs.append(Document(page_content=ch.text, metadata=ch.meta))

    vs = build_vectorstore(args.persist, args.collection, args.embed_model)

    # Prune docs for Swift files that no longer exist on disk
    current_rel_paths = {normalize_path(p, app_dir) for p in swift_files}
    pruned = prune_stale_documents(vs, current_rel_paths)

    upsert_documents(vs, docs)

    # Auto-generate APP_CONTEXT.md after successful indexing
    if args.auto_context:
        try:
            print("\n🔍 Auto-generating APP_CONTEXT.md from indexed code...")
            _generate_app_context(args.persist, args.collection, args.embed_model)
            print("✅ APP_CONTEXT.md updated")
        except Exception as e:
            print(f"⚠️  Failed to generate APP_CONTEXT.md: {e}", file=sys.stderr)
            # Don't fail indexing if context generation fails
    
    print(safe_json({
        "status": "ok",
        "indexed_swift_files": len(swift_files),
        "documents_upserted": len(docs),
        "persist_dir": args.persist,
        "collection": args.collection,
        "stale_paths_pruned": pruned,
        "accessibility_audit": {
            "flagged_screens": len(findings),
            "note": summary["note"],
        },
        "context_generated": args.auto_context,
    }))
    return 0


def cmd_query(args: argparse.Namespace) -> int:
    vs = build_vectorstore(args.persist, args.collection, args.embed_model)
    docs = vs.similarity_search(args.q, k=args.k)

    out = []
    for d in docs:
        out.append({
            "kind": d.metadata.get("kind"),
            "path": d.metadata.get("path"),
            "screen": d.metadata.get("screen") or d.metadata.get("symbol"),
            "snippet": d.page_content[:400] + ("..." if len(d.page_content) > 400 else ""),
        })
    print(safe_json({"q": args.q, "k": args.k, "results": out}))
    return 0


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        prog="python -m rag.cli",
        description="iOS RAG pipeline CLI",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_ingest = sub.add_parser("ingest", help="Ingest a Swift project into Chroma")
    p_ingest.add_argument("--app-dir", required=True, help="Path to iOS app directory")
    p_ingest.add_argument("--persist", required=True, help="Chroma persist directory")
    p_ingest.add_argument("--collection", default="ios_app", help="Chroma collection name")
    p_ingest.add_argument(
        "--embed-model", default=DEFAULT_EMBED_MODEL, help="Embedding model name"
    )
    p_ingest.add_argument(
        "--fail-if-missing-ids",
        action="store_true",
        help="Exit with error if heuristic audit finds screens missing accessibility IDs",
    )
    p_ingest.add_argument(
        "--auto-context",
        action="store_true",
        default=True,
        help="Auto-generate APP_CONTEXT.md after indexing (default: True)",
    )
    p_ingest.add_argument(
        "--no-auto-context",
        dest="auto_context",
        action="store_false",
        help="Skip APP_CONTEXT.md generation",
    )
    p_ingest.set_defaults(func=cmd_ingest)

    p_query = sub.add_parser("query", help="Query the RAG vector store")
    p_query.add_argument("--persist", required=True, help="Chroma persist directory")
    p_query.add_argument("--collection", default="ios_app", help="Chroma collection name")
    p_query.add_argument("--embed-model", default=DEFAULT_EMBED_MODEL)
    p_query.add_argument("--q", required=True, help="Query text")
    p_query.add_argument("--k", type=int, default=8, help="Top-k results")
    p_query.set_defaults(func=cmd_query)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
