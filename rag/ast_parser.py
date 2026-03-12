"""
rag/ast_parser.py

SwiftUI element extraction using tree-sitter AST parsing (with regex fallback).

Extracts interactive UI elements (Button, TextField, Text, Toggle, SecureField,
Picker) from SwiftUI view body code to produce XCTest-ready element queries.
"""
from __future__ import annotations

import re
from typing import Dict, List

# ---------------------------------------------------------------------------
# Element type → XCTest query mapping
# ---------------------------------------------------------------------------

_ELEMENT_TYPE_MAP: Dict[str, str] = {
    "Button":      "buttons",
    "TextField":   "textFields",
    "Text":        "staticTexts",
    "Toggle":      "switches",
    "SecureField": "secureTextFields",
    "Picker":      "pickers",
}

# Supported SwiftUI call targets
_SUPPORTED_CALLS = set(_ELEMENT_TYPE_MAP.keys())

# ---------------------------------------------------------------------------
# Regex-based extraction (tree-sitter fallback / lightweight path)
# ---------------------------------------------------------------------------

# Matches:  Button("Login")  /  TextField("Email", ...)  etc.
# Captures: (ComponentName, first_string_arg)
_CALL_RE = re.compile(
    r'\b(Button|TextField|Text|Toggle|SecureField|Picker)\s*\(\s*"([^"\\]*(?:\\.[^"\\]*)*)"\s*',
    re.MULTILINE,
)

# Also capture label: parameter  e.g.  Toggle("Dark Mode", isOn: $dark)
_LABEL_PARAM_RE = re.compile(
    r'\b(Button|TextField|Text|Toggle|SecureField|Picker)\s*\((?:[^"]*?)label\s*:\s*Text\s*\(\s*"([^"\\]*(?:\\.[^"\\]*)*)"\s*\)',
    re.MULTILINE | re.DOTALL,
)


def _build_entry(component: str, label: str) -> Dict:
    """Build a single element dict from component name and label string."""
    xctest_collection = _ELEMENT_TYPE_MAP.get(component, "otherElements")
    type_key = component.lower()
    return {
        "type": type_key,
        "label": label,
        "query": f'app.{xctest_collection}["{label}"]',
        "confidence": "heuristic",
        "source": "constructor",
    }


def _extract_via_regex(body_code: str) -> List[Dict]:
    """Extract elements using regex patterns (no tree-sitter dependency)."""
    seen: set = set()
    results: List[Dict] = []

    def _add(component: str, label: str) -> None:
        key = (component, label)
        if key not in seen:
            seen.add(key)
            results.append(_build_entry(component, label))

    # Primary: direct string literal as first argument
    for m in _CALL_RE.finditer(body_code):
        _add(m.group(1), m.group(2))

    # Secondary: label: Text("...") pattern (SwiftUI label closures)
    for m in _LABEL_PARAM_RE.finditer(body_code):
        _add(m.group(1), m.group(2))

    return results


def _extract_via_tree_sitter(body_code: str) -> List[Dict] | None:
    """Attempt tree-sitter based extraction; returns None if unavailable."""
    try:
        import tree_sitter  # noqa: F401
        from tree_sitter import Language, Parser  # noqa: F401
    except ImportError:
        return None

    try:
        import tree_sitter_swift  # type: ignore
    except ImportError:
        return None

    try:
        lang = Language(tree_sitter_swift.language())
        parser = Parser(lang)
        tree = parser.parse(body_code.encode())
        root = tree.root_node

        # Query for call_expression nodes whose function is one of our targets
        query_str = "\n".join(
            f'(call_expression function: (simple_identifier) @fn (#eq? @fn "{name}") '
            f'  arguments: (call_suffix (value_arguments (value_argument '
            f'    (line_string_literal (line_str_text) @label))))))'
            for name in _SUPPORTED_CALLS
        )

        query = lang.query(query_str)
        captures = query.captures(root)

        # captures is a list of (node, capture_name) tuples
        seen: set = set()
        results: List[Dict] = []
        fn_nodes: Dict[int, str] = {}  # node id → component name
        label_for_fn: Dict[int, str] = {}

        # Build fn id → name mapping and label mapping
        # Captures alternate: fn node, then label node (per match)
        # Use a pairing strategy: walk captures in order
        fn_pending: list = []
        for node, cap_name in captures:
            if cap_name == "fn":
                fn_pending.append(node)
            elif cap_name == "label" and fn_pending:
                fn_node = fn_pending.pop(0)
                component = fn_node.text.decode() if fn_node.text else ""
                label = node.text.decode() if node.text else ""
                key = (component, label)
                if component in _SUPPORTED_CALLS and key not in seen:
                    seen.add(key)
                    results.append(_build_entry(component, label))

        return results if results else None

    except Exception:
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_swiftui_elements(view_name: str, body_code: str) -> List[Dict]:
    """Extract interactive SwiftUI elements from a view's body code.

    Attempts tree-sitter AST parsing first; falls back to regex extraction
    when tree-sitter or tree-sitter-swift is not installed.

    Args:
        view_name:  The SwiftUI struct/view name (e.g. ``"LoginView"``).
                    Used for logging/debugging; not included in output.
        body_code:  The full text of the SwiftUI view block (struct body).

    Returns:
        A list of element dicts, each with keys:
            - ``type``       – lowercase component name (``"button"``, ``"textfield"``, …)
            - ``label``      – extracted string literal
            - ``query``      – XCTest accessor string (``app.buttons["Login"]``)
            - ``confidence`` – always ``"heuristic"`` (regex/AST, not runtime)
            - ``source``     – always ``"constructor"``

    Example::

        >>> extract_swiftui_elements("LoginView", '''
        ...     Button("Login") { }
        ...     TextField("Email", text: $email)
        ...     SecureField("Password", text: $pwd)
        ... ''')
        [
            {"type": "button",      "label": "Login",    "query": 'app.buttons["Login"]',         "confidence": "heuristic", "source": "constructor"},
            {"type": "textfield",   "label": "Email",    "query": 'app.textFields["Email"]',      "confidence": "heuristic", "source": "constructor"},
            {"type": "securefield", "label": "Password", "query": 'app.secureTextFields["Password"]', "confidence": "heuristic", "source": "constructor"},
        ]
    """
    ts_result = _extract_via_tree_sitter(body_code)
    if ts_result is not None:
        return ts_result
    return _extract_via_regex(body_code)
