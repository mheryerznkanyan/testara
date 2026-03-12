"""
rag/chunker.py

Swift source code chunking: regex patterns, block extraction, and Chunk builder.

This module handles both explicit and inferred accessibility identifiers:
- Explicit: Directly set in code via .accessibilityIdentifier
- Inferred: Generated at runtime from UIView property names via swizzling
  (Format: "ClassName.propertyName")
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Dict, List, Tuple

from rag import ast_parser

from rag.ast_parser import extract_swiftui_elements

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

SWIFTUI_VIEW_START_RE = re.compile(
    r"(?m)^\s*(public|internal|private|fileprivate|open)?\s*struct\s+([A-Za-z_]\w*)\s*:\s*View\s*\{"
)

UIKIT_VC_START_RE = re.compile(
    r"(?m)^\s*(public|internal|private|fileprivate|open)?\s*(final\s+)?class\s+([A-Za-z_]\w*)\s*:\s*([^{\n]*\bUIViewController\b[^{\n]*)\s*\{"
)

SWIFTUI_A11Y_ID_RE = re.compile(r'\.accessibilityIdentifier\(\s*"([^"]+)"\s*\)')
UIKIT_A11Y_ID_RE = re.compile(r'\.accessibilityIdentifier\s*=\s*"([^"]+)"')

SWIFTUI_BUTTON_RE = re.compile(r'Button\(\s*"([^"]+)"\s*\)')

NAV_PATTERNS = [
    re.compile(r"\bnavigationController\?\.\s*pushViewController\s*\(", re.MULTILINE),
    re.compile(r"\bpushViewController\s*\(", re.MULTILINE),
    re.compile(r"\bpresent\s*\(", re.MULTILINE),
    re.compile(r"\bNavigationStack\b", re.MULTILINE),
    re.compile(r"\bnavigationDestination\s*\(", re.MULTILINE),
    re.compile(r"\bsheet\s*\(", re.MULTILINE),
    re.compile(r"\bfullScreenCover\s*\(", re.MULTILINE),
]

SWIFT_CLASS_START_RE = re.compile(
    r"(?m)^\s*(public|internal|private|fileprivate|open)?\s*(final\s+)?class\s+([A-Za-z_]\w*)\s*(?::\s*[^{\n]*)?\s*\{"
)

SWIFT_STRUCT_START_RE = re.compile(
    r"(?m)^\s*(public|internal|private|fileprivate|open)?\s*struct\s+([A-Za-z_]\w*)\s*(?::\s*[^{\n]*)?\s*\{"
)

SWIFTUI_INTERACTIVE_RE = re.compile(
    r"\b(Button|TextField|SecureField|Toggle|Picker)\b", re.MULTILINE
)
UIKIT_INTERACTIVE_RE = re.compile(
    r"\b(UIButton|UITextField|UISwitch|UISegmentedControl|UITableView|UICollectionView)\b",
    re.MULTILINE,
)

# ---------------------------------------------------------------------------
# UIView property extraction for swizzled accessibility IDs
# ---------------------------------------------------------------------------

# Common UIView subclass types that get swizzled at runtime
UIVIEW_TYPES = {
    "UIView", "UILabel", "UIButton", "UITextField", "UIImageView",
    "UITableView", "UICollectionView", "UISwitch", "UITextView",
    "UIScrollView", "WKWebView", "UISegmentedControl", "UISlider",
    "UIStackView", "UIActivityIndicatorView", "UIProgressView",
    "UIPickerView", "UIDatePicker", "UISearchBar", "UIToolbar",
    "UINavigationBar", "UITabBar", "UIPageControl", "UIRefreshControl",
    "MKMapView", "SKView", "MTKView", "ARSCNView", "ARView",
}

# Regex to match property declarations of UIView types
# Matches patterns like:
#   let emailTextField = UITextField()
#   var webView: WKWebView!
#   private let submitButton = UIButton()
#   lazy var tableView: UITableView = { ... }()
UIVIEW_PROPERTY_RE = re.compile(
    r"(?m)^\s*(?:private|fileprivate|internal|public|open)?\s*"
    r"(?:weak|unowned)?\s*"
    r"(?:lazy)?\s*"
    r"(let|var)\s+"
    r"([A-Za-z_]\w*)\s*"
    r"(?::\s*([A-Za-z_]\w+))?",
    re.MULTILINE
)

def extract_uiview_properties(class_name: str, block: str) -> List[str]:
    """Extract UIView property names from a UIViewController class block.

    Delegates to :func:`rag.ast_parser.extract_uikit_properties_ast` for
    accurate, AST-based extraction.  Returns inferred accessibility IDs in
    the format ``"ClassName.propertyName"`` — identical to the previous
    regex-based output so callers remain unchanged.

    Falls back transparently to the legacy regex implementation when
    tree-sitter is unavailable (e.g. in CI without the native binary).

    Parameters
    ----------
    class_name:
        Swift class name (e.g. ``"LoginViewController"``).
    block:
        The full source text of the class block (or the whole file — the
        AST parser will filter by class name regardless).

    Returns
    -------
    List[str]
        Strings of the form ``"ClassName.propertyName"``.
    """
    # --- AST path (preferred) -------------------------------------------
    ast_ids = ast_parser.extract_uiview_property_ids(class_name, block)
    if ast_ids:
        return ast_ids

    # --- Regex fallback (when tree-sitter is unavailable or found nothing) -
    # This preserves behaviour during development / CI without the native lib.
    inferred_ids: List[str] = []

    for match in UIVIEW_PROPERTY_RE.finditer(block):
        prop_name = match.group(2)
        type_annotation = match.group(3)  # May be None for inferred types

        # Get the rest of the line to check for type inference
        line_start = match.start()
        line_end = block.find('\n', line_start)
        if line_end == -1:
            line_end = len(block)
        full_line = block[line_start:line_end]

        is_uiview_type = False

        # Explicit type annotation
        if type_annotation and type_annotation in UIVIEW_TYPES:
            is_uiview_type = True

        # Inferred type from initialiser  (e.g. `= UIButton()`)
        if not is_uiview_type:
            for uiview_type in UIVIEW_TYPES:
                if f"= {uiview_type}(" in full_line or f"= {uiview_type}{{" in full_line:
                    is_uiview_type = True
                    break

        if is_uiview_type:
            inferred_ids.append(f"{class_name}.{prop_name}")

    return inferred_ids


def extract_uiview_properties_detailed(class_name: str, block: str) -> List[Dict]:
    """Return full property dicts (name, type, inferred_id, confidence, source).

    Uses :func:`rag.ast_parser.extract_uikit_properties_ast` directly so
    callers that want richer metadata (confidence, source, resolved type) can
    access it without re-parsing.

    Parameters
    ----------
    class_name:
        Swift class name.
    block:
        Swift source text.

    Returns
    -------
    List[Dict]
        Each dict has keys: ``name``, ``type``, ``inferred_id``,
        ``confidence``, ``source``.  Empty list when tree-sitter is
        unavailable.
    """
    return ast_parser.extract_uikit_properties_ast(class_name, block)


# ---------------------------------------------------------------------------
# Dataclass
# ---------------------------------------------------------------------------

@dataclass
class Chunk:
    text: str
    meta: Dict[str, object]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def meta_list_to_str(items, limit: int = 200) -> str:
    if not items:
        return ""
    return "|".join(str(x) for x in items[:limit])


def _safe_json(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def find_matching_brace(text: str, open_index: int) -> int:
    """Brace matcher that skips braces inside strings and line/block comments.

    Handles:
    - Single-line comments  ``// ...``
    - Block comments        ``/* ... */``
    - Double-quoted strings ``"..."`` with escape sequences
    - Triple-quoted strings ``\"\"\"...\"\"\"`` (Swift multi-line strings)
    """
    depth = 0
    i = open_index
    n = len(text)
    in_line_comment = False
    in_block_comment = False
    in_string = False
    string_triple = False

    while i < n:
        c = text[i]

        # ── line comment ────────────────────────────────────────────────────
        if in_line_comment:
            if c == "\n":
                in_line_comment = False
            i += 1
            continue

        # ── block comment ───────────────────────────────────────────────────
        if in_block_comment:
            if c == "*" and i + 1 < n and text[i + 1] == "/":
                in_block_comment = False
                i += 2
            else:
                i += 1
            continue

        # ── inside string ───────────────────────────────────────────────────
        if in_string:
            if string_triple:
                if text[i : i + 3] == '"""':
                    in_string = False
                    i += 3
                else:
                    i += 1
            else:
                if c == "\\" and i + 1 < n:
                    i += 2  # skip escaped char
                elif c == '"':
                    in_string = False
                    i += 1
                else:
                    i += 1
            continue

        # ── detect comment / string starts ──────────────────────────────────
        if c == "/" and i + 1 < n:
            if text[i + 1] == "/":
                in_line_comment = True
                i += 2
                continue
            if text[i + 1] == "*":
                in_block_comment = True
                i += 2
                continue

        if c == '"':
            if text[i : i + 3] == '"""':
                in_string = True
                string_triple = True
                i += 3
            else:
                in_string = True
                string_triple = False
                i += 1
            continue

        # ── brace counting ──────────────────────────────────────────────────
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1

    return n - 1


def extract_blocks(
    text: str, start_re: re.Pattern, name_group: int, kind: str
) -> List[Tuple[str, str]]:
    """Return [(name, block_text), ...] for each regex match."""
    blocks: List[Tuple[str, str]] = []
    for m in start_re.finditer(text):
        name = m.group(name_group)
        brace_open = text.find("{", m.end() - 1)
        if brace_open == -1:
            continue
        end = find_matching_brace(text, brace_open)
        block = text[m.start(): end + 1].strip()
        blocks.append((name, block))
    return blocks


# ---------------------------------------------------------------------------
# Main chunker
# ---------------------------------------------------------------------------

def build_chunks_for_file(file_text: str, rel_path: str) -> List[Chunk]:
    chunks: List[Chunk] = []

    # SwiftUI View blocks
    for view_name, block in extract_blocks(
        file_text, SWIFTUI_VIEW_START_RE, name_group=2, kind="swiftui_view"
    ):
        a11y_ids = sorted(set(SWIFTUI_A11Y_ID_RE.findall(block)))
        buttons = sorted(set(SWIFTUI_BUTTON_RE.findall(block)))
        nav_hits = sum(1 for pat in NAV_PATTERNS if pat.search(block))

        # Extract SwiftUI elements (Button, TextField, Text, Toggle, SecureField, Picker)
        # via AST / regex for XCTest-ready query generation.
        swiftui_elements = extract_swiftui_elements(view_name, block)

        meta = {
            "kind": "swiftui_view",
            "path": rel_path,
            "screen": view_name,
            "symbol": view_name,
            "accessibility_ids": meta_list_to_str(a11y_ids),
            "accessibility_id_count": len(a11y_ids),
            "buttons": meta_list_to_str(buttons[:50]),
            "button_count": len(buttons),
            "navigation_signals": nav_hits,
            # elements serialised as JSON string for vector store compat
            "elements": _safe_json(swiftui_elements),
            "element_count": len(swiftui_elements),
        }
        chunks.append(Chunk(text=block, meta=meta))

        card = {
            "type": "SCREEN_CARD",
            "ui": "SwiftUI",
            "screen": view_name,
            "path": rel_path,
            "buttons": buttons[:50],
            "accessibility_ids": a11y_ids[:200],
            "has_navigation_signals": bool(nav_hits),
            # Structured element list for downstream consumers
            "elements": swiftui_elements,
        }
        chunks.append(Chunk(text=_safe_json(card), meta={**meta, "kind": "screen_card"}))

    # UIKit ViewController blocks
    for cls_name, block in extract_blocks(
        file_text, UIKIT_VC_START_RE, name_group=3, kind="uikit_viewcontroller"
    ):
        # Extract explicit accessibility IDs set in source code
        explicit_ids = sorted(set(UIKIT_A11Y_ID_RE.findall(block)))

        # Extract inferred accessibility IDs via AST (or regex fallback).
        # `inferred_props` carries full metadata (name, type, confidence, source).
        inferred_props = extract_uiview_properties_detailed(cls_name, block)
        inferred_ids = [p["inferred_id"] for p in inferred_props]

        # Derived metadata for inferred properties
        # confidence is always "inferred"; source is "ast" or "regex" depending
        # on which path produced the result.
        inferred_sources = sorted({p.get("source", "regex") for p in inferred_props})
        inferred_types_map = {p["inferred_id"]: p["type"] for p in inferred_props}

        # Combine explicit and inferred IDs
        all_ids = sorted(set(explicit_ids) | set(inferred_ids))

        nav_hits = sum(1 for pat in NAV_PATTERNS if pat.search(block))
        meta = {
            "kind": "uikit_viewcontroller",
            "path": rel_path,
            "screen": cls_name,
            "symbol": cls_name,
            "accessibility_ids": meta_list_to_str(all_ids),
            "accessibility_id_count": len(all_ids),
            "explicit_accessibility_ids": meta_list_to_str(explicit_ids),
            "inferred_accessibility_ids": meta_list_to_str(inferred_ids),
            # Confidence tag: explicit IDs are "explicit"; inferred are "inferred"
            "inferred_confidence": "inferred" if inferred_ids else "",
            # Source tag: which parser produced the inferred IDs
            "inferred_source": meta_list_to_str(inferred_sources),
            "navigation_signals": nav_hits,
        }
        chunks.append(Chunk(text=block, meta=meta))

        card = {
            "type": "SCREEN_CARD",
            "ui": "UIKit",
            "screen": cls_name,
            "path": rel_path,
            "accessibility_ids": all_ids[:200],
            "explicit_accessibility_ids": explicit_ids[:200],
            # Inferred IDs enriched with type and confidence info
            "inferred_accessibility_ids": [
                {
                    "id": p["inferred_id"],
                    "type": p.get("type", ""),
                    "confidence": p.get("confidence", "inferred"),
                    "source": p.get("source", "regex"),
                }
                for p in inferred_props[:200]
            ],
            "has_navigation_signals": bool(nav_hits),
        }
        chunks.append(Chunk(text=_safe_json(card), meta={**meta, "kind": "screen_card"}))

    # Accessibility map chunk per file
    # Collect explicit IDs from source
    explicit_file_ids = sorted(
        set(SWIFTUI_A11Y_ID_RE.findall(file_text)) | set(UIKIT_A11Y_ID_RE.findall(file_text))
    )
    
    # Collect inferred IDs from all UIKit ViewControllers in the file.
    # Use the detailed extractor so we preserve confidence/source provenance.
    inferred_file_ids = []
    for cls_name, block in extract_blocks(file_text, UIKIT_VC_START_RE, name_group=3, kind=""):
        inferred_file_ids.extend(ast_parser.extract_uiview_property_ids(cls_name, block))
    
    # Combine all IDs for the file
    all_file_ids = sorted(set(explicit_file_ids) | set(inferred_file_ids))
    
    if all_file_ids:
        amap = "ACCESSIBILITY_IDS\npath: " + rel_path + "\n"
        if explicit_file_ids:
            amap += "\n# Explicit IDs (from code):\n" + "\n".join(explicit_file_ids)
        if inferred_file_ids:
            amap += "\n\n# Inferred IDs (runtime swizzling):\n" + "\n".join(sorted(set(inferred_file_ids)))
        
        chunks.append(Chunk(
            text=amap,
            meta={
                "kind": "accessibility_map",
                "path": rel_path,
                "accessibility_ids": meta_list_to_str(all_file_ids),
                "accessibility_id_count": len(all_file_ids),
                "explicit_ids_count": len(explicit_file_ids),
                "inferred_ids_count": len(inferred_file_ids),
            },
        ))

    # Navigation map chunk per file
    nav_lines = []
    for line in file_text.splitlines():
        if any(p.search(line) for p in NAV_PATTERNS):
            nav_lines.append(line.strip())
            if len(nav_lines) >= 60:
                break
    if nav_lines:
        nav_chunk = "NAVIGATION_SIGNALS\npath: " + rel_path + "\n" + "\n".join(nav_lines)
        chunks.append(Chunk(text=nav_chunk, meta={"kind": "navigation_signals", "path": rel_path}))

    # Swift classes (Services, ViewModels, etc.) — skip UIKit VCs already handled above
    vc_names = {name for name, _ in extract_blocks(file_text, UIKIT_VC_START_RE, name_group=3, kind="")}
    for cls_name, block in extract_blocks(
        file_text, SWIFT_CLASS_START_RE, name_group=3, kind="swift_class"
    ):
        if cls_name in vc_names:
            continue
        a11y_ids = sorted(set(SWIFTUI_A11Y_ID_RE.findall(block)) | set(UIKIT_A11Y_ID_RE.findall(block)))
        meta = {
            "kind": "swift_class",
            "path": rel_path,
            "screen": cls_name,
            "symbol": cls_name,
            "accessibility_ids": meta_list_to_str(a11y_ids),
            "accessibility_id_count": len(a11y_ids),
        }
        chunks.append(Chunk(text=block[:4000], meta=meta))

    # Swift structs that are NOT SwiftUI Views (models, configs, etc.)
    view_names = {name for name, _ in extract_blocks(file_text, SWIFTUI_VIEW_START_RE, name_group=2, kind="")}
    for struct_name, block in extract_blocks(
        file_text, SWIFT_STRUCT_START_RE, name_group=2, kind="swift_struct"
    ):
        if struct_name in view_names:
            continue
        meta = {
            "kind": "swift_struct",
            "path": rel_path,
            "screen": struct_name,
            "symbol": struct_name,
        }
        chunks.append(Chunk(text=block[:2000], meta=meta))

    # Fallback: raw slice
    if not chunks:
        raw = file_text.strip()
        if raw:
            chunks.append(Chunk(text=raw[:4000], meta={"kind": "swift_raw", "path": rel_path}))

    return chunks
