"""Validation and prompt-building utilities"""
import re
from collections import defaultdict
from typing import Optional, Dict, List

from app.schemas.test_schemas import AppContext

# Matches auto-injected SwiftUI IDs: {StructName}_{elementType}_{disambiguator}
_AUTO_ID_RE = re.compile(
    r"^([A-Z][A-Za-z0-9]+)_(button|textField|secureField|toggle|tab|"
    r"navigationLink|picker|slider|stepper|datePicker|menu|link|tappableText)_"
)


def _group_ids_by_screen(ids: List[str]) -> str:
    """Group accessibility IDs by screen/struct prefix for clearer LLM context.

    Auto-injected SwiftUI IDs like 'ContentView_tab_settings' are grouped
    under their struct name. UIKit swizzled IDs like 'LoginViewController.submitButton'
    are grouped under the class name. Ungrouped IDs go under 'Other'.
    """
    grouped: Dict[str, List[str]] = defaultdict(list)

    for aid in ids:
        m = _AUTO_ID_RE.match(aid)
        if m:
            grouped[m.group(1)].append(aid)
        elif "." in aid:
            # UIKit swizzled: "ClassName.propertyName"
            cls = aid.split(".", 1)[0]
            grouped[cls].append(aid)
        else:
            grouped["Other"].append(aid)

    lines = []
    for screen in sorted(grouped):
        lines.append(f"  [{screen}]")
        for aid in grouped[screen]:
            lines.append(f"    - {aid}")
    return "\n".join(lines)


def build_context_section(app_context: Optional[AppContext]) -> str:
    """Build the context section for the prompt from AppContext"""
    if not app_context:
        return ""

    sections: List[str] = []

    if app_context.app_name:
        sections.append(f"App Name: {app_context.app_name}")

    if app_context.screens:
        sections.append(f"Available Screens: {', '.join(app_context.screens)}")

    if app_context.ui_elements:
        elements_str = "\n".join(
            [f"  {screen}: {', '.join(elements)}" for screen, elements in app_context.ui_elements.items()]
        )
        sections.append(f"UI Elements:\n{elements_str}")

    if app_context.accessibility_ids:
        grouped = _group_ids_by_screen(app_context.accessibility_ids)
        sections.append(f"Accessibility IDs (grouped by screen):\n{grouped}")

    if app_context.custom_types:
        sections.append(f"Custom Types: {', '.join(app_context.custom_types)}")

    if app_context.source_code_snippets:
        sections.append(f"Relevant Code:\n{app_context.source_code_snippets}")

    return "App Context:\n" + "\n\n".join(sections) if sections else ""


def build_class_name_section(class_name: Optional[str]) -> str:
    """Build the class name section for the prompt"""
    return f"Test Class Name: {class_name}" if class_name else (
        "Generate an appropriate test class name based on the test description."
    )


def sanitize_xcuitest_code(swift_code: str) -> str:
    """Remove forbidden patterns from generated XCUITest code.

    LLMs occasionally emit patterns that the prompt forbids (e.g.
    ``app.otherElements``).  Rather than letting those lines cause runtime
    failures, we strip them in post-processing.
    """
    cleaned_lines: List[str] = []
    skip_next_assert = False

    for line in swift_code.splitlines():
        stripped = line.strip()

        # Skip lines using app.otherElements — they always fail for SwiftUI
        if "otherElements" in stripped:
            # If the next line is an assertion on the variable defined here,
            # we need to skip that too.  Set a flag so the next XCTAssert
            # referencing the same variable is also dropped.
            skip_next_assert = True
            continue

        # If previous line was an otherElements assignment, drop the
        # immediately following assertion that references it.
        if skip_next_assert and stripped.startswith(("XCTAssert", "XCTFail")):
            skip_next_assert = False
            continue
        skip_next_assert = False

        # Remove sleep() calls — prompt says NEVER use sleep
        if re.match(r"^\s*(Thread\.)?sleep\(", stripped):
            continue

        cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


def validate_xcuitest_contract(swift_code: str) -> Dict[str, bool]:
    """Validate that the generated XCUITest code meets required standards"""
    return {
        "has_xcuiapplication": "XCUIApplication()" in swift_code,
        "has_app_launch": "app.launch()" in swift_code,
        "has_wait_for_existence": (
            "waitForExistence(timeout:" in swift_code
            or "XCTNSPredicateExpectation" in swift_code
        ),
        "has_assertions": any(
            x in swift_code
            for x in ["XCTAssertTrue", "XCTAssertEqual", "XCTAssertFalse", "XCTAssertNotNil"]
        ),
        "has_setup_teardown": (
            "setUpWithError" in swift_code and "tearDownWithError" in swift_code
        ),
    }
