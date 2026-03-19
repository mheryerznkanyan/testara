"""Validation and prompt-building utilities"""
import ast
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


def validate_appium_contract(python_code: str) -> Dict[str, bool]:
    """Validate that generated Python Appium test code meets required standards."""
    try:
        tree = ast.parse(python_code)
    except SyntaxError:
        return {
            "syntax_valid": False,
            "has_driver_param": False,
            "has_appium_by": False,
            "has_assertion": False,
            "no_remote_creation": False,
        }

    test_fns = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
    ]

    has_driver_param = any(
        any(arg.arg == "driver" for arg in fn.args.args)
        for fn in test_fns
    )

    return {
        "syntax_valid": True,
        "has_driver_param": has_driver_param,
        "has_appium_by": "AppiumBy" in python_code,
        "has_assertion": "assert " in python_code,
        "no_remote_creation": "webdriver.Remote" not in python_code,
    }
