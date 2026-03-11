"""RAG service - encapsulates vector store lifecycle and querying"""
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


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

    def query(self, test_description: str, k: Optional[int] = None) -> Dict[str, Any]:
        """Query the RAG system for relevant context based on the test description.

        Returns accessibility IDs, code snippets, and screen information.
        Degrades gracefully if the vector store is unavailable.
        """
        if k is None:
            k = self._settings.rag_top_k

        logger.debug("RAG query: %r  k=%d", test_description[:120], k)

        try:
            vs = self._get_vectorstore()
            docs = vs.similarity_search(test_description, k=k)

            accessibility_ids: set = set()
            screens: set = set()
            code_snippets = []

            for doc in docs:
                meta = doc.metadata

                if "accessibility_ids" in meta and meta["accessibility_ids"]:
                    accessibility_ids.update(meta["accessibility_ids"].split("|"))

                if "screen" in meta and meta["screen"]:
                    screens.add(meta["screen"])

                kind = meta.get("kind", "")
                if kind in (
                    "swiftui_view",
                    "accessibility_map",
                    "screen_card",
                    "swift_class",
                    "swift_struct",
                    "uikit_viewcontroller",
                ):
                    code_snippets.append({
                        "kind": kind,
                        "path": meta.get("path", ""),
                        "screen": meta.get("screen", ""),
                        "content": doc.page_content[:1500],
                    })

            result = {
                "accessibility_ids": sorted(accessibility_ids),
                "screens": sorted(screens),
                "code_snippets": code_snippets[:8],
                "total_docs_retrieved": len(docs),
            }
            logger.debug(
                "RAG result: %d accessibility IDs, %d screens, %d snippets",
                len(result["accessibility_ids"]),
                len(result["screens"]),
                len(result["code_snippets"]),
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
