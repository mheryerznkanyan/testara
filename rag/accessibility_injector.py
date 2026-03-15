"""
rag/accessibility_injector.py

Core module for injecting .accessibilityIdentifier() into SwiftUI source files.

Finds interactive SwiftUI elements (Button, TextField, SecureField, Toggle,
.tabItem) that do not yet have .accessibilityIdentifier() and injects
deterministic, predictable names of the form:

    {FileBaseName}_{elementType}_{disambiguator}

Examples:
    FeedScreen_button_feedType
    LoginScreen_textField_username
    ContentView_tab_feed

Used both for in-memory RAG indexing (inject_accessibility_ids) and for
on-disk injection before xcodebuild (inject_directory / restore_files).
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from rag.chunker import (
    find_matching_brace,
    SWIFTUI_VIEW_START_RE,
    SWIFTUI_A11Y_ID_RE,
)

# ---------------------------------------------------------------------------
# Regex patterns for interactive SwiftUI elements
# ---------------------------------------------------------------------------

# Button("Label") { ... }  — label is the first positional string arg
_BUTTON_SIMPLE_RE = re.compile(r'\bButton\s*\(\s*"([^"]*)"')

# Button(action: { ... }) { ... }  — named action parameter
_BUTTON_ACTION_RE = re.compile(r'\bButton\s*\(\s*action\s*:')

# Button { ... } label: { ... }  — action-first trailing-closure form
# (Note: must NOT match Button( variants – the \{ ensures { follows directly)
_BUTTON_CLOSURE_RE = re.compile(r'\bButton\s*\{')

# TextField / SecureField
_TEXTFIELD_RE = re.compile(r'\b(TextField|SecureField)\s*\(\s*"([^"]*)"')

# Toggle
_TOGGLE_RE = re.compile(r'\bToggle\s*\(\s*"([^"]*)"')

# .tabItem { ... }
_TABITEM_RE = re.compile(r'\.tabItem\s*\{')

# Text("Label") inside a closure — for label extraction
_TEXT_LABEL_RE = re.compile(r'\bText\s*\(\s*"([^"]+)"\s*\)')

# How many characters ahead to scan for an existing .accessibilityIdentifier(
_A11Y_LOOK_AHEAD = 500

# New-element keywords that stop the look-ahead scan (avoid false-positive skips)
_NEW_ELEMENT_RE = re.compile(r'\b(Button|TextField|SecureField|Toggle)\b|\.tabItem\b')

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _find_matching_paren(text: str, open_index: int) -> int:
    """Find the closing ) that matches ( at *open_index*.

    Respects strings (single and triple-quoted) and line/block comments,
    mirroring the approach used in :func:`rag.chunker.find_matching_brace`.
    Returns ``len(text) - 1`` as a sentinel if no match is found.
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

        if in_line_comment:
            if c == "\n":
                in_line_comment = False
            i += 1
            continue

        if in_block_comment:
            if c == "*" and i + 1 < n and text[i + 1] == "/":
                in_block_comment = False
                i += 2
            else:
                i += 1
            continue

        if in_string:
            if string_triple:
                if text[i: i + 3] == '"""':
                    in_string = False
                    i += 3
                else:
                    i += 1
            else:
                if c == "\\" and i + 1 < n:
                    i += 2
                elif c == '"':
                    in_string = False
                    i += 1
                else:
                    i += 1
            continue

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
            if text[i: i + 3] == '"""':
                in_string = True
                string_triple = True
                i += 3
            else:
                in_string = True
                string_triple = False
                i += 1
            continue

        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return i
        i += 1

    return n - 1


def _safe_find_brace_end(text: str, brace_pos: int) -> Optional[int]:
    """Wrapper around find_matching_brace that returns None on failure."""
    n = len(text)
    result = find_matching_brace(text, brace_pos)
    if result == n - 1 and (n == 0 or text[result] != "}"):
        return None
    return result


def _safe_find_paren_end(text: str, paren_pos: int) -> Optional[int]:
    """Wrapper around _find_matching_paren that returns None on failure."""
    n = len(text)
    result = _find_matching_paren(text, paren_pos)
    if result == n - 1 and (n == 0 or text[result] != ")"):
        return None
    return result


def _skip_whitespace_forward(text: str, pos: int) -> int:
    """Advance past whitespace (spaces, tabs, newlines) from *pos*."""
    n = len(text)
    while pos < n and text[pos] in " \t\n\r":
        pos += 1
    return pos


def _find_trailing_brace(text: str, after_pos: int) -> Optional[int]:
    """If a ``{`` immediately follows *after_pos* (modulo whitespace), return
    the index of the matching ``}``.  Returns None otherwise."""
    i = _skip_whitespace_forward(text, after_pos)
    if i < len(text) and text[i] == "{":
        return _safe_find_brace_end(text, i)
    return None


def _find_element_end(
    text: str, match_start: int, match_end: int, kind: str
) -> Optional[int]:
    """Determine the *last* character index of an interactive SwiftUI element.

    *kind* is one of:
        ``'button_simple'``   – Button("Label") { ... }
        ``'button_action'``   – Button(action: { ... }) { ... }
        ``'button_closure'``  – Button { ... } label: { ... }
        ``'field'``           – TextField/SecureField("ph", text:)
        ``'toggle'``          – Toggle("label", isOn:)
        ``'tabitem'``         – .tabItem { ... }

    Returns None when the end cannot be determined safely (callers must skip).
    """
    n = len(text)

    # ── .tabItem { ... } ────────────────────────────────────────────────────
    if kind == "tabitem":
        # The regex ends WITH the '{'; it's at match_end - 1.
        brace_pos = match_end - 1
        if brace_pos < 0 or text[brace_pos] != "{":
            # Fallback: find first '{' from match_start
            brace_pos = text.find("{", match_start, match_end)
            if brace_pos == -1:
                return None
        return _safe_find_brace_end(text, brace_pos)

    # ── Button { ... } [label: { ... }] ─────────────────────────────────────
    if kind == "button_closure":
        # Opening action-closure brace is at match_end - 1.
        brace_pos = match_end - 1
        if brace_pos < 0 or text[brace_pos] != "{":
            brace_pos = text.find("{", match_start, match_end)
            if brace_pos == -1:
                return None
        action_end = _safe_find_brace_end(text, brace_pos)
        if action_end is None:
            return None

        # Check for optional  label: { ... }  after the action closure.
        lookahead = text[action_end + 1: min(n, action_end + 80)]
        m = re.match(r"\s*label\s*:\s*\{", lookahead)
        if m:
            label_brace_abs = action_end + 1 + m.end() - 1  # position of '{'
            label_end = _safe_find_brace_end(text, label_brace_abs)
            if label_end is not None:
                return label_end
        return action_end

    # ── Button("Label") { ... }  /  Button(action: { }) { ... } ─────────────
    if kind in ("button_simple", "button_action"):
        paren_pos = text.find("(", match_start)
        if paren_pos == -1:
            return None
        paren_end = _safe_find_paren_end(text, paren_pos)
        if paren_end is None:
            return None

        # Look for a trailing closure { ... } immediately after the )
        trailing = _find_trailing_brace(text, paren_end + 1)
        if trailing is not None:
            return trailing
        return paren_end

    # ── TextField / SecureField / Toggle ─────────────────────────────────────
    if kind in ("field", "toggle"):
        paren_pos = text.find("(", match_start)
        if paren_pos == -1:
            return None
        return _safe_find_paren_end(text, paren_pos)

    return None


def _has_a11y_id_following(text: str, end_pos: int) -> bool:
    """Return True if ``.accessibilityIdentifier(`` appears in the modifier
    chain that immediately follows *end_pos*.

    The scan stops as soon as it encounters the start of a new interactive
    element to avoid falsely attributing the next element's ID to this one.
    """
    window_end = min(len(text), end_pos + 1 + _A11Y_LOOK_AHEAD)
    window = text[end_pos + 1: window_end]

    # Find the earliest start of a new element keyword so we don't look too far.
    stop = len(window)
    m = _NEW_ELEMENT_RE.search(window)
    if m:
        stop = m.start()

    check = window[:stop]
    return ".accessibilityIdentifier(" in check


def _label_to_disambiguator(label: str) -> str:
    """Convert a human-readable label string to a camelCase disambiguator.

    Examples::

        "Feed Type"  -> "feedType"
        "Username"   -> "username"
        "Sign In"    -> "signIn"
        "submit"     -> "submit"
    """
    label = label.strip()
    if not label:
        return ""
    # Split on runs of spaces, hyphens, or underscores.
    words = [w for w in re.split(r"[\s\-_]+", label) if w]
    if not words:
        return ""
    # First word: lowercase first letter, keep the rest.
    first = words[0][0].lower() + words[0][1:] if len(words[0]) > 1 else words[0].lower()
    rest = "".join(w[0].upper() + w[1:] if len(w) > 1 else w.upper() for w in words[1:])
    return first + rest


def _get_line_indent(text: str, pos: int) -> str:
    """Return the leading whitespace of the line that contains *pos*."""
    line_start = text.rfind("\n", 0, pos) + 1  # 0 if no newline found
    indent = []
    for ch in text[line_start:]:
        if ch in (" ", "\t"):
            indent.append(ch)
        else:
            break
    return "".join(indent)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def inject_accessibility_ids(source_text: str, file_stem: str) -> str:
    """Inject ``.accessibilityIdentifier()`` modifiers into SwiftUI source.

    Only operates on files that contain a ``struct X: View`` declaration.
    Interactive elements that already have an ``.accessibilityIdentifier(``
    in their immediately following modifier chain are left untouched.

    Returns the (possibly modified) source text.  The original is returned
    unchanged when no injections are needed or when the file is not a SwiftUI
    view file.

    Naming convention: ``{file_stem}_{elementType}_{disambiguator}``
        * *elementType*: ``button``, ``textField``, ``secureField``,
          ``toggle``, ``tab``
        * *disambiguator*: camelCase from the element label, or a numeric
          index when no label is available.

    Examples::

        FeedScreen_button_feedType
        LoginScreen_textField_username
        ContentView_tab_feed
        ProfileScreen_button_0      # fallback when label cannot be extracted
    """
    # Guard: only process SwiftUI view files.
    if not SWIFTUI_VIEW_START_RE.search(source_text):
        return source_text

    # ── Collect candidate elements ───────────────────────────────────────────
    # Each entry: (start, match_end, element_type_name, internal_kind, label)
    candidates: List[Tuple[int, int, str, str, str]] = []

    for m in _BUTTON_SIMPLE_RE.finditer(source_text):
        candidates.append((m.start(), m.end(), "button", "button_simple", m.group(1)))

    for m in _BUTTON_ACTION_RE.finditer(source_text):
        # Only add if _BUTTON_SIMPLE_RE didn't already match at the same position.
        candidates.append((m.start(), m.end(), "button", "button_action", ""))

    for m in _BUTTON_CLOSURE_RE.finditer(source_text):
        # _BUTTON_CLOSURE_RE only fires when '{' follows Button directly (no '(')
        candidates.append((m.start(), m.end(), "button", "button_closure", ""))

    for m in _TEXTFIELD_RE.finditer(source_text):
        etype = "textField" if m.group(1) == "TextField" else "secureField"
        candidates.append((m.start(), m.end(), etype, "field", m.group(2)))

    for m in _TOGGLE_RE.finditer(source_text):
        candidates.append((m.start(), m.end(), "toggle", "toggle", m.group(1)))

    for m in _TABITEM_RE.finditer(source_text):
        # Try to extract label from Text("...") inside the .tabItem { } block.
        brace_pos = m.end() - 1  # position of opening '{'
        tab_label = ""
        block_end = _safe_find_brace_end(source_text, brace_pos)
        if block_end is not None:
            block_content = source_text[brace_pos: block_end + 1]
            tm = _TEXT_LABEL_RE.search(block_content)
            if tm:
                tab_label = tm.group(1)
        candidates.append((m.start(), m.end(), "tab", "tabitem", tab_label))

    # Sort by start position so we process from top to bottom.
    candidates.sort(key=lambda x: x[0])

    # Deduplicate: remove candidates whose start overlaps with a previously
    # confirmed element's extent (handles the rare regex-overlap edge case).
    confirmed_ranges: List[Tuple[int, int]] = []  # (start, end_pos)

    def _overlaps(start: int) -> bool:
        for rs, re_ in confirmed_ranges:
            if rs <= start <= re_:
                return True
        return False

    # ── Determine injection points ───────────────────────────────────────────
    # Per-type tracking for deterministic naming.
    type_index: Dict[str, int] = {}          # etype -> total seen count
    type_labels_seen: Dict[str, Set[str]] = {}  # etype -> set of disambiguators used

    injections: List[Tuple[int, str]] = []   # (end_pos, text_to_insert)

    for start, match_end, etype, kind, label in candidates:
        if _overlaps(start):
            continue

        end_pos = _find_element_end(source_text, start, match_end, kind)
        if end_pos is None:
            continue

        confirmed_ranges.append((start, end_pos))

        # Skip if an accessibilityIdentifier already follows this element.
        if _has_a11y_id_following(source_text, end_pos):
            # Still count it so indices stay stable for later elements.
            type_index.setdefault(etype, 0)
            type_index[etype] += 1
            continue

        # ── Build the accessibility ID ───────────────────────────────────────
        type_index.setdefault(etype, 0)
        type_labels_seen.setdefault(etype, set())

        raw_disambiguator = _label_to_disambiguator(label)

        if raw_disambiguator:
            # Resolve collisions by appending the occurrence index.
            if raw_disambiguator not in type_labels_seen[etype]:
                disambiguator = raw_disambiguator
            else:
                disambiguator = f"{raw_disambiguator}{type_index[etype]}"
            type_labels_seen[etype].add(disambiguator)
        else:
            # Numeric fallback: FeedScreen_button_0
            disambiguator = str(type_index[etype])

        type_index[etype] += 1

        a11y_id = f"{file_stem}_{etype}_{disambiguator}"

        # Match the indentation of the element's own line.
        indent = _get_line_indent(source_text, start)
        injection_text = f'\n{indent}.accessibilityIdentifier("{a11y_id}")'

        injections.append((end_pos, injection_text))

    if not injections:
        return source_text

    # ── Apply injections back-to-front so earlier offsets stay valid ─────────
    result = source_text
    for end_pos, inj in sorted(injections, key=lambda x: x[0], reverse=True):
        result = result[: end_pos + 1] + inj + result[end_pos + 1:]

    return result


def inject_directory(
    root: Path, exclude_dirs: Optional[Set[str]] = None
) -> Dict[str, str]:
    """Walk *root* for ``.swift`` files and inject accessibility IDs in-place.

    Files are only modified when:
    * They end with ``.swift``.
    * They are not inside any directory listed in *exclude_dirs*.
    * They contain the string ``'View'`` (quick pre-filter).
    * :func:`inject_accessibility_ids` actually changes them.

    Returns a ``{filepath_str: original_content}`` backup dict that can be
    passed to :func:`restore_files` to undo all changes.

    Parameters
    ----------
    root:
        Directory to walk recursively.
    exclude_dirs:
        Directory names (not full paths) to skip.  Defaults to a standard
        iOS build-noise set: ``Pods``, ``.git``, ``build``, ``DerivedData``,
        ``.build``, ``vendor``.
    """
    if exclude_dirs is None:
        exclude_dirs = {"Pods", ".git", "build", "DerivedData", ".build", "vendor"}

    backup: Dict[str, str] = {}

    for dirpath, dirs, files in os.walk(root):
        # Prune excluded / hidden directories in-place.
        dirs[:] = [
            d for d in dirs if d not in exclude_dirs and not d.startswith(".")
        ]

        for fname in files:
            if not fname.endswith(".swift"):
                continue

            fpath = Path(dirpath) / fname

            try:
                original = fpath.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue

            # Quick pre-filter: skip files with no 'View' reference.
            if "View" not in original:
                continue

            modified = inject_accessibility_ids(original, fpath.stem)

            if modified != original:
                backup[str(fpath)] = original
                try:
                    fpath.write_text(modified, encoding="utf-8")
                except OSError:
                    # If we can't write, drop from backup so restore is a no-op.
                    backup.pop(str(fpath), None)

    return backup


def restore_files(backup: Dict[str, str]) -> None:
    """Restore Swift files to their pre-injection content.

    Parameters
    ----------
    backup:
        The dict returned by :func:`inject_directory` (``{filepath_str:
        original_content}``).
    """
    for filepath_str, original_content in backup.items():
        try:
            Path(filepath_str).write_text(original_content, encoding="utf-8")
        except OSError:
            pass  # Best-effort; caller should handle critical failures.
