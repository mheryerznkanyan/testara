"""
rag/ast_parser.py

Tree-sitter–based AST parser for Swift UIKit source code.

Purpose
-------
Replace fragile regex-based UIView property extraction with a proper
AST walk using the tree-sitter-swift grammar.  This gives us:

  - Correct handling of nested braces, generics, closures
  - Property wrappers (@IBOutlet, @Published, custom wrappers)
  - Optionals (Type?, Type!)
  - Lazy stored properties  (lazy var foo: Type = ...)
  - Closure-initialised properties  (lazy var foo: Type = { ... }())
  - Generic types  (UITableView<Model>, Array<UIView>, etc.)
  - Accurate confidence labels ("inferred") and source tags ("ast")

Public API
----------
    extract_uikit_properties_ast(class_name, source_code) -> List[Dict]

Each returned dict has the shape::

    {
        "name":        str,          # Swift property name
        "type":        str,          # Resolved Swift type string (best effort)
        "inferred_id": str,          # "<ClassName>.<propertyName>"
        "confidence":  "inferred",   # Always "inferred" for swizzled IDs
        "source":      "ast",        # Provenance tag
    }

Graceful degradation
--------------------
If tree-sitter or tree-sitter-swift is not installed the module falls
back to an empty list (with a logged warning) so the rest of the RAG
pipeline is unaffected.  Import errors are caught once at module load
time; subsequent calls are no-ops rather than exceptions.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Attempt tree-sitter import once at module load
# ---------------------------------------------------------------------------

_TS_AVAILABLE = False
_SWIFT_LANGUAGE = None

try:
    import tree_sitter_swift as _ts_swift  # type: ignore[import]
    from tree_sitter import Language, Parser  # type: ignore[import]

    _SWIFT_LANGUAGE = Language(_ts_swift.language())
    _TS_AVAILABLE = True
    logger.debug("tree-sitter-swift grammar loaded successfully")
except Exception as _e:  # ImportError or any binding error
    logger.warning(
        "tree-sitter or tree-sitter-swift not available – "
        "falling back to empty property list. (%s)", _e
    )


# ---------------------------------------------------------------------------
# UIView type registry
# ---------------------------------------------------------------------------

#: UIKit / MapKit / Metal / AR types that receive swizzled accessibility IDs
#: at runtime.  Extend as needed.
UIVIEW_TYPES: frozenset[str] = frozenset({
    "UIView", "UILabel", "UIButton", "UITextField", "UIImageView",
    "UITableView", "UICollectionView", "UISwitch", "UITextView",
    "UIScrollView", "WKWebView", "UISegmentedControl", "UISlider",
    "UIStackView", "UIActivityIndicatorView", "UIProgressView",
    "UIPickerView", "UIDatePicker", "UISearchBar", "UIToolbar",
    "UINavigationBar", "UITabBar", "UIPageControl", "UIRefreshControl",
    "MKMapView", "SKView", "MTKView", "ARSCNView", "ARView",
})


# ---------------------------------------------------------------------------
# Tree-sitter query
# ---------------------------------------------------------------------------

# We query for *all* property_declaration nodes inside a class_declaration
# whose supertype chain contains UIViewController.  Post-filtering on the
# UIView type happens in Python once we have the raw text.
#
# The query below captures:
#   @capture("prop")  – the entire property_declaration node
#
# Note: tree-sitter-swift represents property declarations as
# `property_declaration` nodes.  We walk upward in Python to verify the
# enclosing class matches `class_name`.
_PROPERTY_QUERY_SRC = """
(property_declaration) @prop
"""


# ---------------------------------------------------------------------------
# Helper: build parser once and reuse
# ---------------------------------------------------------------------------

def _make_parser() -> "Parser":
    """Return a configured Swift tree-sitter Parser instance."""
    parser = Parser(_SWIFT_LANGUAGE)
    return parser


# One shared parser per process (not thread-safe for concurrent mutation,
# but parse() calls are fine when not sharing the same parser object
# across threads simultaneously).
_PARSER: Optional["Parser"] = _make_parser() if _TS_AVAILABLE else None


# ---------------------------------------------------------------------------
# AST walking helpers
# ---------------------------------------------------------------------------

def _node_text(node, source_bytes: bytes) -> str:
    """Return the raw source text for a tree-sitter Node."""
    return source_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="replace")


def _find_enclosing_class(node) -> Optional[str]:
    """Walk up the tree from *node* and return the nearest class name, or None."""
    current = node.parent
    while current is not None:
        if current.type == "class_declaration":
            # The class name is the first `type_identifier` child
            for child in current.children:
                if child.type == "type_identifier":
                    return child.type  # type string — we need the text
        current = current.parent
    return None


def _get_enclosing_class_name(node, source_bytes: bytes) -> Optional[str]:
    """Return the text of the nearest enclosing class_declaration name."""
    current = node.parent
    while current is not None:
        if current.type == "class_declaration":
            for child in current.children:
                if child.type == "type_identifier":
                    return source_bytes[child.start_byte:child.end_byte].decode("utf-8", errors="replace")
        current = current.parent
    return None


def _extract_property_name(prop_node, source_bytes: bytes) -> Optional[str]:
    """
    Extract the property (variable binding) name from a property_declaration node.

    Swift grammar structure (simplified)::

        (property_declaration
          modifiers: ...
          (value_binding_pattern
            (pattern (simple_identifier))
          )
          type_annotation: ...
          initializer: ...
        )

    or directly::

        (property_declaration
          (pattern (simple_identifier))
          ...
        )
    """
    # Walk children looking for a pattern → simple_identifier
    for child in prop_node.children:
        if child.type in ("value_binding_pattern", "pattern"):
            for sub in child.children:
                if sub.type == "simple_identifier":
                    return _node_text(sub, source_bytes)
                # pattern may nest: (pattern (simple_identifier))
                for subsub in sub.children:
                    if subsub.type == "simple_identifier":
                        return _node_text(subsub, source_bytes)
        # Direct simple_identifier at property level (some grammar versions)
        if child.type == "simple_identifier":
            return _node_text(child, source_bytes)
    return None


def _extract_type_annotation(prop_node, source_bytes: bytes) -> Optional[str]:
    """
    Extract the declared type from a type_annotation child, e.g. `UILabel?` or
    `UITableView<MyCell>`.

    Returns the raw type text (stripped of leading `: `).
    """
    for child in prop_node.children:
        if child.type == "type_annotation":
            # type_annotation ::= ":" <type>
            # Skip the colon token and return the rest
            parts = []
            for sub in child.children:
                if sub.type == ":":
                    continue
                parts.append(_node_text(sub, source_bytes).strip())
            return " ".join(parts).strip() if parts else None
    return None


def _extract_inferred_type(prop_node, source_bytes: bytes) -> Optional[str]:
    """
    Try to infer the type from the initialiser expression when there is no
    explicit type annotation.

    Handles patterns like::

        let submitButton = UIButton()
        lazy var tableView = UITableView(frame: .zero)

    Returns just the type name (e.g. ``"UIButton"``) or None.
    """
    raw = _node_text(prop_node, source_bytes)
    # Look for `= SomeType(` or `= SomeType {`
    import re
    m = re.search(r"=\s*([A-Za-z_]\w*)\s*[({]", raw)
    if m:
        return m.group(1)
    return None


def _type_base(type_str: str) -> str:
    """Strip optionals and generics to get the bare type name.

    Examples::
        "UILabel?"      -> "UILabel"
        "UILabel!"      -> "UILabel"
        "UITableView<Cell>" -> "UITableView"
    """
    # Remove optional/IUO suffixes
    base = type_str.rstrip("?!")
    # Remove generic parameters
    angle = base.find("<")
    if angle != -1:
        base = base[:angle]
    return base.strip()


def _has_property_wrapper(prop_node, source_bytes: bytes) -> Optional[str]:
    """
    Return the first property wrapper name if present (e.g. ``"IBOutlet"``),
    otherwise None.

    Swift grammar encodes ``@IBOutlet`` as an ``attribute`` node child of the
    property_declaration.
    """
    for child in prop_node.children:
        if child.type == "attribute":
            # attribute ::= "@" user_type arguments?
            for sub in child.children:
                if sub.type in ("user_type", "simple_identifier", "type_identifier"):
                    return _node_text(sub, source_bytes)
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_uikit_properties_ast(
    class_name: str,
    source_code: str,
) -> List[Dict[str, str]]:
    """Extract UIView property declarations from a UIViewController class via AST.

    Uses the tree-sitter-swift grammar to parse *source_code* and locate
    ``property_declaration`` nodes that belong to the class named *class_name*
    **and** whose declared/inferred type is a known UIView subclass.

    Parameters
    ----------
    class_name:
        The Swift class name to filter on (e.g. ``"LoginViewController"``).
    source_code:
        Full Swift source text containing the class definition.

    Returns
    -------
    List[Dict[str, str]]
        One dict per matching property::

            {
                "name":        "submitButton",
                "type":        "UIButton",
                "inferred_id": "LoginViewController.submitButton",
                "confidence":  "inferred",
                "source":      "ast",
            }

        Returns an empty list if tree-sitter is unavailable, the class is not
        found, or no matching UIView properties exist.

    Notes
    -----
    * ``confidence`` is always ``"inferred"`` because these IDs are generated
      at runtime by swizzling, not set explicitly in source.
    * Handles: property wrappers, optional/IUO types, lazy vars, closure
      initialisers, and generic types.
    * The function is safe to call multiple times; the parser is reused.
    """
    if not _TS_AVAILABLE or _PARSER is None:
        logger.debug(
            "tree-sitter unavailable; returning empty property list for %s", class_name
        )
        return []

    if not source_code or not source_code.strip():
        return []

    source_bytes = source_code.encode("utf-8")

    # Parse the source
    try:
        tree = _PARSER.parse(source_bytes)
    except Exception as exc:
        logger.warning("tree-sitter parse error for %s: %s", class_name, exc)
        return []

    # Run the property query
    try:
        query = _SWIFT_LANGUAGE.query(_PROPERTY_QUERY_SRC)
        captures = query.captures(tree.root_node)
    except Exception as exc:
        logger.warning("tree-sitter query error for %s: %s", class_name, exc)
        return []

    results: List[Dict[str, str]] = []

    # captures is dict[str, list[Node]] in tree-sitter >= 0.22
    prop_nodes = captures.get("prop", [])

    for prop_node in prop_nodes:
        # ── 1. Verify this property belongs to our target class ──────────
        enclosing = _get_enclosing_class_name(prop_node, source_bytes)
        if enclosing != class_name:
            continue

        # ── 2. Extract property name ─────────────────────────────────────
        prop_name = _extract_property_name(prop_node, source_bytes)
        if not prop_name:
            logger.debug("Could not extract property name from node: %s",
                         _node_text(prop_node, source_bytes)[:80])
            continue

        # ── 3. Resolve type (annotation takes priority over inferred) ────
        type_str = _extract_type_annotation(prop_node, source_bytes)
        if not type_str:
            type_str = _extract_inferred_type(prop_node, source_bytes)

        if not type_str:
            # Can't determine type — skip
            continue

        base_type = _type_base(type_str)

        # ── 4. Check if it's a UIView subclass ───────────────────────────
        if base_type not in UIVIEW_TYPES:
            continue

        # ── 5. Collect optional wrapper info for debug/future use ────────
        wrapper = _has_property_wrapper(prop_node, source_bytes)
        logger.debug(
            "Found UIView property: %s.%s : %s  wrapper=%s",
            class_name, prop_name, type_str, wrapper
        )

        results.append({
            "name":        prop_name,
            "type":        type_str,          # full type as written (e.g. "UILabel?")
            "inferred_id": f"{class_name}.{prop_name}",
            "confidence":  "inferred",
            "source":      "ast",
        })

    return results


# ---------------------------------------------------------------------------
# Convenience: extract just the inferred_id strings (for chunker compat)
# ---------------------------------------------------------------------------

def extract_uiview_property_ids(class_name: str, source_code: str) -> List[str]:
    """Return a list of inferred accessibility ID strings.

    Thin wrapper around :func:`extract_uikit_properties_ast` that returns
    only the ``inferred_id`` values, matching the shape expected by the
    original regex-based ``extract_uiview_properties()`` function.

    Parameters
    ----------
    class_name:
        Swift class name (e.g. ``"LoginViewController"``).
    source_code:
        Full Swift source text.

    Returns
    -------
    List[str]
        Strings of the form ``"ClassName.propertyName"``.
    """
    props = extract_uikit_properties_ast(class_name, source_code)
    return [p["inferred_id"] for p in props]
