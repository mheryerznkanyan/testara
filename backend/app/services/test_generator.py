"""Test Generator service — LLM-powered Appium Python test generation."""
import ast
import logging
import re
from typing import Any, Dict, Optional

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
    text = re.sub(r"\n?```\s*$", "", text)
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

    def _build_runtime_context_section(self, snapshot) -> str:
        if snapshot is None:
            return ""
        tree_str = snapshot.to_context_string()
        if not tree_str or "No interactive elements" in tree_str:
            return ""
        return f"{RUNTIME_TREE_INSTRUCTIONS}\n\n{tree_str}\n"

    def run(self, request: TestGenerationRequest, accessibility_snapshot=None, retry_context: Optional[str] = None) -> TestGenerationResponse:
        """Generate an Appium Python test function from the request."""
        context_section = build_context_section(request.app_context)
        class_name_section = build_class_name_section(request.class_name)
        runtime_section = self._build_runtime_context_section(accessibility_snapshot)

        if accessibility_snapshot and accessibility_snapshot.interactive_elements():
            logger.info(
                "Using runtime accessibility tree: %d interactive elements",
                len(accessibility_snapshot.interactive_elements()),
            )

        logger.info("Attempt with retry context: %s", retry_context[:100] if retry_context else "none")

        retry_section = f"\n{retry_context}\n" if retry_context else ""

        user_message = (
            f"Generate an Appium Python test function for the following:\n\n"
            f"Test Description: {request.test_description}\n\n"
            f"{runtime_section}"
            f"{context_section}\n\n"
            f"{class_name_section}\n\n"
            f"Include comments: {request.include_comments}\n\n"
            f"{retry_section}"
            "Output ONLY Python code."
        )

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
            },
        )
