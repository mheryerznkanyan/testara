"""
rag/chunker.py

Swift source code chunking: regex patterns, block extraction, and Chunk builder.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Dict, List, Tuple

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
        }
        chunks.append(Chunk(text=_safe_json(card), meta={**meta, "kind": "screen_card"}))

    # UIKit ViewController blocks
    for cls_name, block in extract_blocks(
        file_text, UIKIT_VC_START_RE, name_group=3, kind="uikit_viewcontroller"
    ):
        a11y_ids = sorted(set(UIKIT_A11Y_ID_RE.findall(block)))
        nav_hits = sum(1 for pat in NAV_PATTERNS if pat.search(block))
        meta = {
            "kind": "uikit_viewcontroller",
            "path": rel_path,
            "screen": cls_name,
            "symbol": cls_name,
            "accessibility_ids": meta_list_to_str(a11y_ids),
            "accessibility_id_count": len(a11y_ids),
            "navigation_signals": nav_hits,
        }
        chunks.append(Chunk(text=block, meta=meta))

        card = {
            "type": "SCREEN_CARD",
            "ui": "UIKit",
            "screen": cls_name,
            "path": rel_path,
            "accessibility_ids": a11y_ids[:200],
            "has_navigation_signals": bool(nav_hits),
        }
        chunks.append(Chunk(text=_safe_json(card), meta={**meta, "kind": "screen_card"}))

    # Accessibility map chunk per file
    file_ids = sorted(
        set(SWIFTUI_A11Y_ID_RE.findall(file_text)) | set(UIKIT_A11Y_ID_RE.findall(file_text))
    )
    if file_ids:
        amap = "ACCESSIBILITY_IDS\npath: " + rel_path + "\n" + "\n".join(file_ids)
        chunks.append(Chunk(
            text=amap,
            meta={
                "kind": "accessibility_map",
                "path": rel_path,
                "accessibility_ids": meta_list_to_str(file_ids),
                "accessibility_id_count": len(file_ids),
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
