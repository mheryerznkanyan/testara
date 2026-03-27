"""Test Generator service — LLM-powered Appium Python test generation."""
import ast
import logging
import re
from typing import Any, Dict

try:
    from langsmith import traceable
    from langsmith.run_helpers import get_current_run_tree
    _LANGSMITH_AVAILABLE = True
except ImportError:
    def traceable(**kwargs):
        def decorator(fn): return fn
        return decorator
    def get_current_run_tree(): return None
    _LANGSMITH_AVAILABLE = False

from langchain_core.messages import HumanMessage, SystemMessage
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.prompts import APPIUM_PYTEST_SYSTEM_PROMPT, RUNTIME_TREE_INSTRUCTIONS
from app.schemas.test_schemas import TestGenerationRequest, TestGenerationResponse
from app.utils.validators import (
    build_class_name_section,
    build_context_section,
    validate_appium_contract,
)

logger = logging.getLogger(__name__)


def _strip_python_fences(text: str) -> str:
    """Remove ```python ... ``` or ``` ... ``` fences from LLM output."""
    text = text.strip()
    text = re.sub(r"^```python\s*\n?", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^```\s*\n?", "", text)
    # Remove trailing fences (may have whitespace or newlines after)
    text = re.sub(r"\n?```[\s]*$", "", text)
    # Also remove any standalone ``` lines anywhere at the end
    while text.rstrip().endswith("```"):
        text = text.rstrip()[:-3].rstrip()
    return text.strip()


def _extract_fn_name(python_code: str) -> str:
    """Extract the first test_ function name from generated code."""
    try:
        tree = ast.parse(python_code)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                return node.name
    except SyntaxError:
        pass
    return "test_generated"


class TestGenerator:
    """Generates Appium Python test functions via LLM."""

    def __init__(self, llm):
        self._llm = llm

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type(Exception),
        retry_error_callback=lambda retry_state: (_ for _ in ()).throw(
            retry_state.outcome.exception()
        ),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def _invoke_llm(self, messages):
        return self._llm.invoke(messages)

    def _filter_relevant_screens(self, snapshot, description: str):
        """Return a filtered snapshot with only screens relevant to the test description."""
        from app.utils.accessibility_tree_parser import MultiScreenSnapshot, ScreenCapture

        if not hasattr(snapshot, 'screens') or not snapshot.screens:
            return snapshot

        desc_lower = description.lower()
        keywords = set(desc_lower.split())

        scored_screens = []
        for screen in snapshot.screens:
            label_lower = screen.screen_label.lower()
            # Always include Home (starting point for navigation)
            if label_lower == "home":
                scored_screens.append((1000, screen))
                continue

            score = 0
            # Match screen label against description (high weight)
            for word in label_lower.replace(">", " ").split():
                word = word.strip()
                if word and word in keywords:
                    score += 100
            # Bonus if full screen label phrase appears in description
            for part in label_lower.split(">"):
                part = part.strip()
                if part and part in desc_lower:
                    score += 200

            # Match element names against description (low weight, capped)
            elem_score = 0
            for e in screen.interactive_elements():
                name_lower = e.name.lower()
                if name_lower in desc_lower:
                    elem_score += 5
                if elem_score >= 20:
                    break  # cap element matching to avoid large screens dominating

            score += elem_score

            if score > 0:
                scored_screens.append((score, screen))

        # Sort by relevance, take top screens (Home + up to 5 most relevant)
        scored_screens.sort(key=lambda x: x[0], reverse=True)
        selected = [s for _, s in scored_screens[:6]]

        if not selected:
            # No match — just send Home + first 2 screens as fallback
            selected = snapshot.screens[:3]

        logger.info(
            "Filtered %d → %d relevant screens for: %r",
            len(snapshot.screens), len(selected), description[:60],
        )

        return MultiScreenSnapshot(
            screens=selected,
            bundle_id=snapshot.bundle_id,
            device_udid=snapshot.device_udid,
        )

    def _build_runtime_context_section(self, snapshot, description: str = "") -> str:
        if snapshot is None:
            return ""
        if description:
            snapshot = self._filter_relevant_screens(snapshot, description)
        tree_str = snapshot.to_context_string()
        if not tree_str or "No interactive elements" in tree_str:
            return ""
        return f"{RUNTIME_TREE_INSTRUCTIONS}\n\n{tree_str}\n"

    @traceable(name="generate-test")
    def run(self, request: TestGenerationRequest, accessibility_snapshot=None) -> TestGenerationResponse:
        """Generate an Appium Python test function from the request."""
        context_section = build_context_section(request.app_context)
        class_name_section = build_class_name_section(request.class_name)
        runtime_section = self._build_runtime_context_section(
            accessibility_snapshot, request.test_description
        )

        if accessibility_snapshot and accessibility_snapshot.interactive_elements():
            logger.info(
                "Using runtime accessibility tree: %d interactive elements",
                len(accessibility_snapshot.interactive_elements()),
            )

        # Build user message — prioritize discovery tree, include RAG context only if present
        parts = [
            f"Generate an Appium Python test function for:\n\n"
            f"Test Description: {request.test_description}\n",
        ]
        if runtime_section:
            parts.append(runtime_section)
        if context_section and "Known Accessibility IDs:" in context_section:
            # RAG context has useful data — include it
            parts.append(context_section)
        parts.append(f"{class_name_section}")
        if request.include_comments:
            parts.append("Include inline comments explaining each step.")
        parts.append("Output ONLY Python code.")

        user_message = "\n\n".join(parts)

        messages = [
            SystemMessage(content=APPIUM_PYTEST_SYSTEM_PROMPT),
            HumanMessage(content=user_message),
        ]

        logger.info("Invoking LLM for Appium test: %r", request.test_description[:80])
        ai_msg = self._invoke_llm(messages)
        test_code = _strip_python_fences(ai_msg.content)

        fn_name = _extract_fn_name(test_code)

        checks = validate_appium_contract(test_code)
        validation_results: Dict[str, Any] = {
            **checks,
            "all_passed": all(checks.values()),
            "failed_checks": [k for k, v in checks.items() if not v],
        }

        logger.info(
            "Test generated: fn=%s  validation=%s",
            fn_name,
            "OK" if validation_results["all_passed"] else validation_results["failed_checks"],
        )

        # Capture LangSmith run ID for feedback linking
        langsmith_run_id = None
        try:
            run_tree = get_current_run_tree()
            if run_tree:
                langsmith_run_id = str(run_tree.id)
        except Exception:
            pass

        return TestGenerationResponse(
            test_code=test_code,
            test_type="ui",
            class_name=fn_name,
            metadata={
                "provider": "langchain_anthropic",
                "language": "python",
                "has_context": bool(request.app_context),
                "context_provided": bool(context_section),
                "contract_validation": validation_results,
                "langsmith_run_id": langsmith_run_id,
            },
        )
