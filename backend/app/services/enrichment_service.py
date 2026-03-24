"""EnrichmentService — expands a brief test description into a precise test specification."""
import logging
from pathlib import Path

try:
    from langsmith import traceable
except ImportError:
    def traceable(**kwargs):
        def decorator(fn): return fn
        return decorator

from langchain_core.messages import HumanMessage, SystemMessage
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.prompts import ENRICHMENT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

# Descriptions shorter than this are always sent for enrichment.
# Longer ones are still enriched, but the original is preserved in metadata.
_MIN_ENRICH_LENGTH = 0


class EnrichmentService:
    """Uses the LLM to rewrite a vague test description into a precise specification.

    The LLM is injected at construction time (same instance as TestGenerator).
    """

    def __init__(self, llm, app_context_path: str = None):
        self._llm = llm
        self._app_context = self._load_app_context(app_context_path)
    
    def _load_app_context(self, context_path: str = None) -> str:
        """Load app context from file if available"""
        if context_path and Path(context_path).exists():
            try:
                with open(context_path, 'r') as f:
                    context = f.read()
                logger.info(f"Loaded app context from {context_path}")
                return context
            except Exception as e:
                logger.warning(f"Failed to load app context: {e}")
                return ""
        
        # Try rag_store location first, then repo root
        rag_store_path = Path(__file__).parent.parent.parent.parent / "rag_store" / "APP_CONTEXT.md"
        if rag_store_path.exists():
            try:
                with open(rag_store_path, 'r') as f:
                    context = f.read()
                logger.info(f"Loaded app context from {rag_store_path}")
                return context
            except Exception as e:
                logger.warning(f"Failed to load app context from rag_store: {e}")

        default_path = Path(__file__).parent.parent.parent.parent / "APP_CONTEXT.md"
        if default_path.exists():
            try:
                with open(default_path, 'r') as f:
                    context = f.read()
                logger.info(f"Loaded app context from {default_path}")
                return context
            except Exception as e:
                logger.warning(f"Failed to load default app context: {e}")
        
        return ""

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type(Exception),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def _invoke_llm(self, messages):
        return self._llm.invoke(messages)

    @traceable(name="enrich-description")
    def enrich(self, description: str) -> dict:
        """Enrich a test description and return both versions.

        Args:
            description: Raw user-supplied test description.

        Returns:
            dict with keys:
                - ``original``  : the original description unchanged.
                - ``enriched``  : the LLM-expanded description.
                - ``used``      : always True (enrichment was attempted).
                - ``error``     : present only if enrichment failed; in that case
                                  ``enriched`` falls back to ``original``.
        """
        original = description.strip()

        # Build context-aware prompt
        context_section = ""
        if self._app_context:
            context_section = f"\n\nAPP CONTEXT:\n{self._app_context}\n\n"
        
        messages = [
            SystemMessage(content=ENRICHMENT_SYSTEM_PROMPT + context_section),
            HumanMessage(
                content=(
                    f"Enrich this iOS test description:\n\n{original}\n\n"
                    "Use the app context above to make the enriched description more specific and relevant to this app. "
                    "Return only the enriched description text."
                )
            ),
        ]

        try:
            logger.info("Enriching test description: %r", original[:80])
            response = self._invoke_llm(messages)
            enriched = response.content.strip()
            logger.info("Enriched description: %r", enriched[:120])
            return {"original": original, "enriched": enriched, "used": True}
        except Exception as exc:
            logger.error("Enrichment failed, using original description: %s", exc)
            return {
                "original": original,
                "enriched": original,
                "used": True,
                "error": str(exc),
            }
