"""
rag/store.py

Chroma vector store helpers: build, upsert, prune stale docs, and file-system utilities.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Iterable, List, Set

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings

logger = logging.getLogger(__name__)

EXCLUDE_DIRS = {
    ".git",
    "Pods",
    "Carthage",
    "DerivedData",
    ".build",
    ".swiftpm",
    "Build",
    ".xcodeproj",
    ".xcworkspace",
}

SWIFT_SUFFIX = ".swift"


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def sha1(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8", errors="ignore")).hexdigest()


def read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def normalize_path(p: Path, root: Path) -> str:
    try:
        return str(p.relative_to(root)).replace("\\", "/")
    except Exception:
        return str(p).replace("\\", "/")


def iter_swift_files(root: Path) -> Iterable[Path]:
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith(".")]
        for f in files:
            if f.endswith(SWIFT_SUFFIX):
                yield Path(dirpath) / f


def meta_list_to_str(items, limit: int = 200) -> str:
    if not items:
        return ""
    return "|".join(str(x) for x in items[:limit])


def safe_json(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


# ---------------------------------------------------------------------------
# Vector store
# ---------------------------------------------------------------------------

def build_vectorstore(persist_dir: str, collection: str, embed_model: str) -> Chroma:
    embeddings = HuggingFaceEmbeddings(model_name=embed_model)
    return Chroma(
        collection_name=collection,
        embedding_function=embeddings,
        persist_directory=persist_dir,
    )


def upsert_documents(vs: Chroma, docs: List[Document]) -> None:
    """Upsert documents using deterministic IDs for stable re-ingestion.

    Note: Chroma >= 0.4 auto-persists; no explicit persist() call needed.
    """
    ids = [sha1(d.page_content + safe_json(d.metadata)) for d in docs]
    vs.add_documents(documents=docs, ids=ids)
    logger.info("Upserted %d documents into vector store.", len(docs))


def get_indexed_paths(vs: Chroma) -> Set[str]:
    """Return the set of file paths currently stored in the vector store."""
    try:
        result = vs.get(include=["metadatas"])
        paths: Set[str] = set()
        for meta in result.get("metadatas") or []:
            path = meta.get("path", "")
            if path and path != "_audit_":
                paths.add(path)
        return paths
    except Exception as exc:
        logger.warning("Could not retrieve indexed paths: %s", exc)
        return set()


def delete_documents_by_paths(vs: Chroma, paths: Set[str]) -> int:
    """Delete all documents whose 'path' metadata matches any of the given paths.

    Returns the number of paths for which deletions were attempted.
    """
    if not paths:
        return 0

    deleted_count = 0
    for path in paths:
        try:
            result = vs.get(where={"path": path}, include=["metadatas"])
            ids = result.get("ids") or []
            if ids:
                vs.delete(ids=ids)
                logger.info("Deleted %d stale chunks for path: %s", len(ids), path)
                deleted_count += 1
        except Exception as exc:
            logger.warning("Failed to delete docs for path '%s': %s", path, exc)

    return deleted_count


def prune_stale_documents(vs: Chroma, current_paths: Set[str]) -> int:
    """Remove vector store documents for files that no longer exist on disk.

    Args:
        vs: The Chroma vector store instance.
        current_paths: Relative paths of Swift files currently on disk.

    Returns:
        Number of stale paths pruned.
    """
    indexed = get_indexed_paths(vs)
    stale = indexed - current_paths
    if stale:
        logger.info("Pruning %d stale paths from vector store.", len(stale))
    return delete_documents_by_paths(vs, stale)
