"""Test Generator service - LLM-powered Swift test generation"""
import logging
from typing import TYPE_CHECKING, Any, Dict, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.prompts import RUNTIME_TREE_INSTRUCTIONS, XCTEST_SYSTEM_PROMPT, XCUITEST_SYSTEM_PROMPT

if TYPE_CHECKING:
    from app.utils.accessibility_tree_parser import AccessibilitySnapshot, MultiScreenSnapshot
from app.schemas.test_schemas import TestGenerationRequest, TestGenerationResponse
from app.utils.swift_utils import extract_class_name, strip_code_fences
from app.utils.validators import (
    build_class_name_section,
    build_context_section,
    validate_xcuitest_contract,
)

logger = logging.getLogger(__name__)


def _is_retryable(exc: BaseException) -> bool:
    """Return True for transient LLM errors worth retrying (rate-limits, timeouts)."""
    msg = str(exc).lower()
    return any(
        kw in msg
        for kw in ("rate limit", "overloaded", "529", "timeout", "connection", "503", "502")
    )


class TestGenerator:
    """Test generator using LangChain and Claude — LLM is injected, not constructed here."""

    def __init__(self, llm):
        self._llm = llm

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type(Exception),
        retry_error_callback=lambda retry_state: (_ for _ in ()).throw(retry_state.outcome.exception()),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def _invoke_llm(self, messages):
        """Invoke the LLM with up to 3 retries on transient errors."""
        return self._llm.invoke(messages)

    def _build_runtime_context_section(self, snapshot) -> str:
        """Build the runtime tree context section for the user message."""
        if snapshot is None:
            return ""
        tree_str = snapshot.to_context_string()
        if not tree_str or "No interactive elements" in tree_str:
            return ""
        return f"{RUNTIME_TREE_INSTRUCTIONS}\n\n{tree_str}\n"

    def run(self, request: TestGenerationRequest, accessibility_snapshot=None) -> TestGenerationResponse:
        """Generate a Swift XCTest/XCUITest based on the request.

        Args:
            request: TestGenerationRequest containing test description and context.
            accessibility_snapshot: Optional AccessibilitySnapshot from live Appium discovery.

        Returns:
            TestGenerationResponse with generated Swift code.

        Raises:
            ValueError: If test_type is invalid.
        """
        test_type = request.test_type.lower().strip()
        if test_type not in {"unit", "ui"}:
            raise ValueError("test_type must be 'unit' or 'ui'")

        system_prompt = XCTEST_SYSTEM_PROMPT if test_type == "unit" else XCUITEST_SYSTEM_PROMPT

        # Inject launch environment into setup template if configured
        from app.core.config import settings
        if settings.launch_environment and test_type == "ui":
            env_lines = []
            for pair in settings.launch_environment.split(","):
                pair = pair.strip()
                if "=" in pair:
                    key, value = pair.split("=", 1)
                    env_lines.append(f'    app.launchEnvironment["{key.strip()}"] = "{value.strip()}"')
            if env_lines:
                env_block = "\n".join(env_lines)
                system_prompt = system_prompt.replace(
                    '    app.launch()\n}',
                    f'{env_block}\n    app.launch()\n}}',
                )
        default_class_name = "GeneratedUnitTests" if test_type == "unit" else "GeneratedUITests"

        context_section = build_context_section(request.app_context)
        class_name_section = build_class_name_section(request.class_name)
        runtime_section = self._build_runtime_context_section(accessibility_snapshot)

        if accessibility_snapshot and accessibility_snapshot.interactive_elements():
            logger.info(
                "Using runtime accessibility tree: %d interactive elements",
                len(accessibility_snapshot.interactive_elements()),
            )

        test_label = "XCTest unit test" if test_type == "unit" else "XCUITest UI test"
        user_message = (
            f"Generate a Swift {test_label} for the following:\n\n"
            f"Test Description: {request.test_description}\n\n"
            f"{runtime_section}"
            f"{context_section}\n\n"
            f"{class_name_section}\n\n"
            f"Include comments: {request.include_comments}\n\n"
            "Output ONLY Swift code."
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message),
        ]

        logger.info("Invoking LLM for %s test: %r", test_type, request.test_description[:80])
        ai_msg = self._invoke_llm(messages)
        swift_code = strip_code_fences(ai_msg.content)

        final_class_name = extract_class_name(swift_code, request.class_name or default_class_name)

        validation_results: Dict[str, Any] = {}
        if test_type == "ui":
            checks = validate_xcuitest_contract(swift_code)
            validation_results = {
                **checks,
                "all_passed": all(checks.values()),
                "failed_checks": [k for k, v in checks.items() if not v],
            }

        logger.info("Test generated: class=%s type=%s", final_class_name, test_type)

        return TestGenerationResponse(
            swift_code=swift_code,
            test_type=test_type,
            class_name=final_class_name,
            metadata={
                "provider": "langchain_anthropic",
                "has_context": bool(request.app_context),
                "context_provided": bool(context_section),
                "contract_validation": validation_results if test_type == "ui" else None,
            },
        )
