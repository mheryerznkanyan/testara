"""Suite generator — uses LLM to generate test descriptions from discovery snapshot."""
import json
import logging
from typing import List

from langchain_core.messages import HumanMessage, SystemMessage

try:
    from langsmith import traceable
except ImportError:
    def traceable(**kwargs):
        def decorator(fn): return fn
        return decorator

from app.core.prompts import SUITE_GENERATION_PROMPT
from app.utils.accessibility_tree_parser import MultiScreenSnapshot

logger = logging.getLogger(__name__)


class SuiteGenerator:
    """Generates test descriptions from a multi-screen discovery snapshot."""

    def __init__(self, llm):
        self._llm = llm

    @traceable(name="generate-test-suite-descriptions")
    def generate_descriptions(
        self, snapshot: MultiScreenSnapshot, count: int = 25
    ) -> List[str]:
        """Use LLM to generate test descriptions from discovered screens."""
        tree_context = snapshot.to_context_string()
        if not tree_context or "No screens captured" in tree_context:
            logger.warning("No discovery data available for suite generation")
            return []

        prompt = SUITE_GENERATION_PROMPT.format(
            count=count,
            tree_context=tree_context,
        )

        logger.info(
            "Generating %d test descriptions from %d screens...",
            count,
            len(snapshot.screens),
        )

        response = self._llm.invoke([
            SystemMessage(content="You are a JSON-only output assistant."),
            HumanMessage(content=prompt),
        ])

        # Parse JSON array from response
        text = response.content.strip()
        # Strip markdown fences if present
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        text = text.strip()

        try:
            descriptions = json.loads(text)
            if not isinstance(descriptions, list):
                logger.error("LLM returned non-list JSON: %s", type(descriptions))
                return []
            descriptions = [d for d in descriptions if isinstance(d, str) and d.strip()]
            logger.info("Generated %d test descriptions", len(descriptions))
            return descriptions[:count]
        except json.JSONDecodeError as e:
            logger.error("Failed to parse LLM response as JSON: %s\nResponse: %s", e, text[:500])
            return []
