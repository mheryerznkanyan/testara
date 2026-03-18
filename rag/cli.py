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
from rag.localization_parser import build_localization_chunks
from rag.storyboard_parser import extract_storyboard_ids
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

_STORYBOARD_SUFFIXES = {".storyboard", ".xib"}
_LOCALIZATION_SUFFIXES = {".xcstrings", ".strings"}
_EXCLUDE_DIRS = {"Pods", ".git", "build", "DerivedData", ".build", "vendor"}


def _iter_storyboard_files(root: Path):
    """Yield all .storyboard and .xib files under *root*, skipping noise dirs."""
    import os
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in _EXCLUDE_DIRS and not d.startswith(".")]
        for f in files:
            if Path(f).suffix.lower() in _STORYBOARD_SUFFIXES:
                yield Path(dirpath) / f


def _iter_localization_files(root: Path):
    """Yield all .xcstrings and .strings files under *root*, skipping noise dirs."""
    import os
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in _EXCLUDE_DIRS and not d.startswith(".")]
        for f in files:
            if Path(f).suffix.lower() in _LOCALIZATION_SUFFIXES:
                yield Path(dirpath) / f


def _resolve_localized_strings(swift_text: str, l10n_map: dict) -> str:
    """Inject resolved localization values as inline comments in Swift code.

    Transforms:
        String(localized: "feed.type.new", bundle: .main)
    Into:
        String(localized: "feed.type.new", bundle: .main) /* → "New" */

    This lets the LLM see the actual displayed UI text directly in the code
    context, eliminating the need to cross-reference a separate localization chunk.
    """
    import re

    def _replace(m: re.Match) -> str:
        full = m.group(0)
        key = m.group(1)
        value = l10n_map.get(key)
        if value:
            return f'{full} /* → "{value}" */'
        return full

    # Match String(localized: "key") with optional extra params like bundle:
    return re.sub(
        r'String\s*\(\s*localized\s*:\s*"([^"]+)"[^)]*\)',
        _replace,
        swift_text,
    )


def _generate_app_context(persist_dir: str, collection: str, embed_model: str):
    """Generate APP_CONTEXT.md after indexing.

    Uses the *persist_dir* that was just populated by ``cmd_ingest`` so
    that the RAG query reads from the correct store regardless of CWD.
    """
    import sys
    from pathlib import Path

    backend_path = Path(__file__).parent.parent / "backend"
    if str(backend_path) not in sys.path:
        sys.path.insert(0, str(backend_path))

    from app.core.config import settings
    from app.services.rag_service import RAGService
    from app.services.context_extractor import AppContextExtractor

    # Override rag_persist_dir so RAGService reads from the store we just
    # wrote to — not whatever relative path settings resolved to.
    settings.rag_persist_dir = str(Path(persist_dir).resolve())
    settings.rag_collection = collection

    rag_service = RAGService(settings=settings)
    extractor = AppContextExtractor(rag_service)

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

    # ── Pre-parse localization files to resolve strings in Swift chunks ─────
    from rag.localization_parser import parse_xcstrings, parse_localizable_strings
    l10n_map: dict[str, str] = {}
    for loc_path in _iter_localization_files(app_dir):
        try:
            suffix = loc_path.suffix.lower()
            if suffix == ".xcstrings":
                l10n_map.update(parse_xcstrings(loc_path))
            elif suffix == ".strings":
                l10n_map.update(parse_localizable_strings(loc_path))
        except Exception:
            pass
    # ────────────────────────────────────────────────────────────────────────

    for p in swift_files:
        rel = normalize_path(p, app_dir)
        text = read_text(p)
        if not text.strip():
            continue
        # Resolve localized strings inline so the LLM sees actual UI text
        if l10n_map:
            text = _resolve_localized_strings(text, l10n_map)
        all_chunks.extend(build_chunks_for_file(text, rel))

    # ── Storyboard / XIB ingestion ──────────────────────────────────────────
    storyboard_chunks: List[Chunk] = []
    storyboard_files = list(_iter_storyboard_files(app_dir))
    for sb_path in storyboard_files:
        rel = normalize_path(sb_path, app_dir)
        try:
            vc_map = extract_storyboard_ids(str(sb_path))
        except (FileNotFoundError, OSError, ValueError) as exc:
            print(f"WARNING: skipping {rel}: {exc}", file=sys.stderr)
            continue

        for vc_class, ids in vc_map.items():
            if not ids:
                continue
            card = safe_json({
                "type": "STORYBOARD_IDS",
                "source": "storyboard",
                "path": rel,
                "viewController": vc_class,
                "accessibility_ids": ids,
            })
            storyboard_chunks.append(Chunk(
                text=card,
                meta={
                    "kind": "storyboard_ids",
                    "path": rel,
                    "screen": vc_class,
                    "symbol": vc_class,
                    "source": "storyboard",
                    "confidence": "explicit",
                    "accessibility_ids": "|".join(ids),
                    "accessibility_id_count": len(ids),
                },
            ))

    all_chunks.extend(storyboard_chunks)
    # ────────────────────────────────────────────────────────────────────────

    # ── Localization file ingestion (.xcstrings, .strings) ─────────────────
    localization_chunks: List[Chunk] = []
    localization_files = list(_iter_localization_files(app_dir))
    for loc_path in localization_files:
        rel = normalize_path(loc_path, app_dir)
        try:
            localization_chunks.extend(build_localization_chunks(loc_path, rel))
        except Exception as exc:
            print(f"WARNING: skipping {rel}: {exc}", file=sys.stderr)

    all_chunks.extend(localization_chunks)
    # ────────────────────────────────────────────────────────────────────────

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

    # Prune docs for files that no longer exist on disk
    current_rel_paths = {normalize_path(p, app_dir) for p in swift_files}
    current_rel_paths |= {normalize_path(p, app_dir) for p in storyboard_files}
    current_rel_paths |= {normalize_path(p, app_dir) for p in localization_files}
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
        "indexed_storyboard_files": len(storyboard_files),
        "indexed_localization_files": len(localization_files),
        "storyboard_chunks": len(storyboard_chunks),
        "localization_chunks": len(localization_chunks),
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
