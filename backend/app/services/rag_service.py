"""RAG service - encapsulates vector store lifecycle and querying"""
import logging
import re
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)

# Matches auto-injected SwiftUI IDs to extract the struct/screen name
_AUTO_ID_SCREEN_RE = re.compile(
    r"^([A-Z][A-Za-z0-9]+)_(button|textField|secureField|toggle|tab|"
    r"navigationLink|picker|slider|stepper|datePicker|menu|link|tappableText)_"
)


class RAGService:
    """Encapsulates Chroma vector store; lazily initialized on first use."""

    def __init__(self, settings):
        self._settings = settings
        self._vectorstore = None

    def _get_vectorstore(self):
        if self._vectorstore is None:
            from langchain_chroma import Chroma
            from langchain_huggingface import HuggingFaceEmbeddings

            logger.info(
                "Initialising vector store: collection=%s persist=%s",
                self._settings.rag_collection,
                self._settings.rag_persist_dir,
            )
            embeddings = HuggingFaceEmbeddings(model_name=self._settings.rag_embed_model)
            self._vectorstore = Chroma(
                collection_name=self._settings.rag_collection,
                embedding_function=embeddings,
                persist_directory=self._settings.rag_persist_dir,
            )
        return self._vectorstore

    @staticmethod
    def _extract_docs(
        docs,
        accessibility_ids: Set[str],
        screens: Set[str],
        code_snippets: List[Dict[str, Any]],
        seen_paths: Set[str],
    ) -> None:
        """Extract metadata from retrieved docs into the accumulator sets/lists."""
        for doc in docs:
            meta = doc.metadata

            if "accessibility_ids" in meta and meta["accessibility_ids"]:
                accessibility_ids.update(meta["accessibility_ids"].split("|"))

            if "screen" in meta and meta["screen"]:
                screens.add(meta["screen"])

            kind = meta.get("kind", "")
            doc_key = f"{kind}:{meta.get('path', '')}:{meta.get('screen', '')}"
            if kind in (
                "swiftui_view",
                "accessibility_map",
                "screen_card",
                "swift_class",
                "swift_struct",
                "uikit_viewcontroller",
            ) and doc_key not in seen_paths:
                seen_paths.add(doc_key)
                code_snippets.append({
                    "kind": kind,
                    "path": meta.get("path", ""),
                    "screen": meta.get("screen", ""),
                    "content": doc.page_content[:1500],
                })

    @staticmethod
    def _extract_referenced_screens(
        accessibility_ids: Set[str], screens: Set[str]
    ) -> Set[str]:
        """Derive screen names referenced by auto-injected IDs but not yet retrieved.

        For example, if we found ``ContentView_tab_settings`` we know a
        "Settings"-related screen exists.  We generate plausible View/Screen
        names to query for in a supplementary pass.
        """
        known = {s.lower() for s in screens}
        candidates: Set[str] = set()

        for aid in accessibility_ids:
            m = _AUTO_ID_SCREEN_RE.match(aid)
            if not m:
                continue
            struct_name = m.group(1)
            etype = m.group(2)
            # The struct that owns this ID is already a known screen
            if struct_name.lower() not in known:
                candidates.add(struct_name)

            # For tab/navigationLink, the disambiguator hints at a destination
            if etype in ("tab", "navigationLink"):
                # e.g. ContentView_tab_settings → "settings"
                suffix = aid.split(f"_{etype}_", 1)[-1]
                if suffix:
                    # Generate plausible screen names from the disambiguator
                    cap = suffix[0].upper() + suffix[1:]
                    for variant in (f"{cap}View", f"{cap}Screen", cap):
                        if variant.lower() not in known:
                            candidates.add(variant)

        return candidates

    def query(self, test_description: str, k: Optional[int] = None) -> Dict[str, Any]:
        """Query the RAG system for relevant context based on the test description.

        Returns accessibility IDs, code snippets, and screen information.
        Performs supplementary queries for related screens (e.g., tab/navigation
        destinations) to ensure the LLM has context for all screens involved.
        Degrades gracefully if the vector store is unavailable.
        """
        if k is None:
            k = self._settings.rag_top_k

        logger.debug("RAG query: %r  k=%d", test_description[:120], k)

        try:
            vs = self._get_vectorstore()
            docs = vs.similarity_search(test_description, k=k)

            accessibility_ids: Set[str] = set()
            screens: Set[str] = set()
            code_snippets: List[Dict[str, Any]] = []
            seen_paths: Set[str] = set()

            self._extract_docs(docs, accessibility_ids, screens, code_snippets, seen_paths)

            logger.info(
                "Initial RAG: %d docs, %d a11y IDs, %d screens, kinds=%s",
                len(docs),
                len(accessibility_ids),
                len(screens),
                [d.metadata.get("kind", "") for d in docs],
            )

            # ── Supplementary retrieval for related screens ──────────────
            # If initial results reference screens we haven't retrieved
            # (e.g., tab destinations), fetch their elements too.
            related_screens = self._extract_referenced_screens(accessibility_ids, screens)
            total_retrieved = len(docs)

            if related_screens:
                logger.info(
                    "Supplementary RAG queries for related screens: %s",
                    sorted(related_screens),
                )
                for screen_name in related_screens:
                    try:
                        extra_docs = vs.similarity_search(
                            f"{screen_name} screen view accessibility elements",
                            k=4,
                        )
                        self._extract_docs(
                            extra_docs, accessibility_ids, screens,
                            code_snippets, seen_paths,
                        )
                        total_retrieved += len(extra_docs)
                    except Exception as exc:
                        logger.warning(
                            "Supplementary query for %r failed: %s",
                            screen_name, exc,
                        )

            result = {
                "accessibility_ids": sorted(accessibility_ids),
                "screens": sorted(screens),
                "code_snippets": code_snippets[:12],
                "total_docs_retrieved": total_retrieved,
            }
            logger.info(
                "RAG result: %d accessibility IDs, %d screens, %d snippets. IDs: %s",
                len(result["accessibility_ids"]),
                len(result["screens"]),
                len(result["code_snippets"]),
                result["accessibility_ids"][:20],  # log first 20 for debugging
            )
            return result

        except Exception as exc:
            logger.error("RAG query failed: %s", exc, exc_info=True)
            return {
                "accessibility_ids": [],
                "screens": [],
                "code_snippets": [],
                "total_docs_retrieved": 0,
                "error": str(exc),
            }

    def status(self) -> Dict[str, Any]:
        """Return vector store health info (doc count, collection, persist dir)."""
        try:
            vs = self._get_vectorstore()
            collection = vs._collection  # Chroma internal attr
            count = collection.count()
            return {
                "status": "ok",
                "collection": self._settings.rag_collection,
                "persist_dir": self._settings.rag_persist_dir,
                "document_count": count,
            }
        except Exception as exc:
            logger.warning("RAG status check failed: %s", exc)
            return {
                "status": "unavailable",
                "collection": self._settings.rag_collection,
                "persist_dir": self._settings.rag_persist_dir,
                "error": str(exc),
            }
