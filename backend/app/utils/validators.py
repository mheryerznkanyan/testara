"""Validation and prompt-building utilities"""
from typing import Optional, Dict, List

from app.schemas.test_schemas import AppContext


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
        sections.append(f"Accessibility IDs: {', '.join(app_context.accessibility_ids)}")

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
