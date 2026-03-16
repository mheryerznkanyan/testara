"""
rag/accessibility_injector.py

Core module for injecting .accessibilityIdentifier() into SwiftUI source files.

Finds interactive SwiftUI elements (Button, TextField, SecureField, Toggle,
.tabItem, NavigationLink, Picker, Slider, Stepper, DatePicker, Menu, Link)
that do not yet have .accessibilityIdentifier() and injects deterministic,
predictable names of the form:

    {StructName}_{elementType}_{disambiguator}

When the enclosing ``struct X: View`` can be determined, *StructName* is used
instead of the file stem so that files containing multiple views produce
unambiguous identifiers.

Examples:
    LoginScreen_button_logOut          (from Button("Log Out"))
    LoginScreen_textField_username     (from TextField("Username", ...))
    MainView_tab_settings              (from .tabItem { Image(systemName: "gear") })
    ListScreen_button_select_\\(item)  (Button inside ForEach)
    SettingsScreen_picker_language     (from Picker("Language", ...))
    PlayerView_slider_volume           (from Slider(value: $volume))

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

# NavigationLink("Label") or NavigationLink(destination:) { ... }
_NAVLINK_SIMPLE_RE = re.compile(r'\bNavigationLink\s*\(\s*"([^"]*)"')
_NAVLINK_DEST_RE = re.compile(r'\bNavigationLink\s*\(\s*destination\s*:')
_NAVLINK_CLOSURE_RE = re.compile(r'\bNavigationLink\s*\{')

# Picker("Label", selection:)
_PICKER_RE = re.compile(r'\bPicker\s*\(\s*"([^"]*)"')

# Slider(value: $binding)
_SLIDER_RE = re.compile(r'\bSlider\s*\(')

# Stepper("Label", ...)
_STEPPER_RE = re.compile(r'\bStepper\s*\(\s*"([^"]*)"')

# DatePicker("Label", ...)
_DATEPICKER_RE = re.compile(r'\bDatePicker\s*\(\s*"([^"]*)"')

# Menu("Label") { ... }
_MENU_RE = re.compile(r'\bMenu\s*\(\s*"([^"]*)"')

# Link("Label", destination:)
_LINK_RE = re.compile(r'\bLink\s*\(\s*"([^"]*)"')

# Text("Label") inside a closure — for label extraction
_TEXT_LABEL_RE = re.compile(r'\bText\s*\(\s*"([^"]+)"\s*\)')

# Label("title", systemImage:) inside a closure — for label extraction
_LABEL_RE = re.compile(r'\bLabel\s*\(\s*"([^"]+)"')

# Image(systemName: "icon") inside a closure — fallback label extraction
_IMAGE_SYSTEM_RE = re.compile(r'\bImage\s*\(\s*systemName\s*:\s*"([^"]+)"\s*\)')

# Image("assetName") — named asset image (not systemName)
_IMAGE_NAMED_RE = re.compile(r'\bImage\s*\(\s*"([^"]+)"\s*\)')

# Text("...").onTapGesture { ... } — tappable text
_TEXT_TAP_RE = re.compile(r'\bText\s*\(\s*"([^"]+)"\s*\)')

# $binding extraction from value:/text:/selection: parameters
_BINDING_RE = re.compile(r'(?:value|text|selection)\s*:\s*\$(\w+)')

# ForEach detection — captures the loop variable name
_FOREACH_RE = re.compile(r'\bForEach\s*\([^)]*\)\s*\{[^}]*?\b(\w+)\s+in\b', re.DOTALL)
# Simplified ForEach — ForEach(items) { item in
_FOREACH_SIMPLE_RE = re.compile(r'\bForEach\b[^{]*\{\s*(\w+)\s+in\b')

# Common SF Symbol name → semantic label mapping (generic, not app-specific)
_SF_SYMBOL_LABELS: dict[str, str] = {
    "house": "home", "house.fill": "home",
    "gear": "settings", "gearshape": "settings", "gearshape.fill": "settings",
    "person": "profile", "person.fill": "profile",
    "person.circle": "profile", "person.circle.fill": "profile",
    "magnifyingglass": "search",
    "bell": "notifications", "bell.fill": "notifications",
    "envelope": "mail", "envelope.fill": "mail",
    "heart": "favorites", "heart.fill": "favorites",
    "star": "favorites", "star.fill": "favorites",
    "bookmark": "bookmarks", "bookmark.fill": "bookmarks",
    "book": "bookmarks", "book.fill": "bookmarks",
    "cart": "cart", "cart.fill": "cart",
    "bag": "bag", "bag.fill": "bag",
    "map": "map", "map.fill": "map",
    "location": "location", "location.fill": "location",
    "camera": "camera", "camera.fill": "camera",
    "photo": "photos", "photo.fill": "photos",
    "photo.on.rectangle": "photos",
    "message": "messages", "message.fill": "messages",
    "bubble.left": "chat", "bubble.left.fill": "chat",
    "phone": "phone", "phone.fill": "phone",
    "newspaper": "news", "newspaper.fill": "news",
    "doc": "documents", "doc.fill": "documents",
    "folder": "files", "folder.fill": "files",
    "trash": "delete", "trash.fill": "delete",
    "pencil": "edit", "pencil.circle": "edit",
    "plus": "add", "plus.circle": "add", "plus.circle.fill": "add",
    "minus": "remove", "minus.circle": "remove",
    "xmark": "close", "xmark.circle": "close", "xmark.circle.fill": "close",
    "checkmark": "done", "checkmark.circle": "done", "checkmark.circle.fill": "done",
    "arrow.left": "back", "chevron.left": "back",
    "arrow.right": "forward", "chevron.right": "forward",
    "square.and.arrow.up": "share",
    "ellipsis": "more", "ellipsis.circle": "more",
    "info.circle": "info", "info.circle.fill": "info",
    "questionmark.circle": "help",
    "exclamationmark.triangle": "warning",
    "play": "play", "play.fill": "play",
    "pause": "pause", "pause.fill": "pause",
    "stop": "stop", "stop.fill": "stop",
    "music.note": "music",
    "video": "video", "video.fill": "video",
    "link": "link",
    "wifi": "wifi",
    "globe": "web",
    "clock": "history", "clock.fill": "history",
    "calendar": "calendar",
    "list.bullet": "list",
    "square.grid.2x2": "grid", "square.grid.2x2.fill": "grid",
}

# Matches auto-injected .accessibilityIdentifier("FileName_type_disambiguator")
# Pattern: optional leading newline+whitespace, then the modifier call.
# The ID follows the convention: Word_word_word (with optional \(var) suffix).
_AUTO_INJECTED_A11Y_RE = re.compile(
    r'\n[ \t]*\.accessibilityIdentifier\("'
    r'[A-Z]\w*_(?:button|textField|secureField|toggle|tab'
    r'|navigationLink|picker|slider|stepper|datePicker|menu|link|tappableText)_[\w]+'
    r'(?:_\d+)?'           # optional collision suffix (_2, _3, …)
    r'(?:_\\?\([^)]*\))?'  # optional \(variable) interpolation
    r'"\)'
)

# How many characters ahead to scan for an existing .accessibilityIdentifier(
_A11Y_LOOK_AHEAD = 500

# New-element keywords that stop the look-ahead scan (avoid false-positive skips)
_NEW_ELEMENT_RE = re.compile(
    r'\b(Button|TextField|SecureField|Toggle|NavigationLink|Picker'
    r'|Slider|Stepper|DatePicker|Menu|Link)\b|\.tabItem\b'
)

# Container-like element types that need .accessibilityElement(true) to be
# discoverable by XCUITest (analogous to UITableViewCell/UICollectionViewCell
# handling in the UIKit runtime injector).
_CONTAINER_ELEMENT_TYPES = frozenset({"navigationLink", "menu"})

# Struct X: View pattern — used to determine the enclosing view struct name.
_STRUCT_VIEW_RE = re.compile(
    r'\bstruct\s+(\w+)\s*:\s*[^{]*\bView\b[^{]*\{'
)

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

    # ── TextField / SecureField / Toggle / Picker / Stepper / DatePicker /
    #    Menu / Link / Slider ──────────────────────────────────────────────
    if kind in ("field", "toggle", "picker", "stepper", "datepicker",
                "link", "slider"):
        paren_pos = text.find("(", match_start)
        if paren_pos == -1:
            return None
        paren_end = _safe_find_paren_end(text, paren_pos)
        if paren_end is None:
            return None
        # Picker / Menu often have a trailing content closure { ... }
        if kind in ("picker", "menu"):
            trailing = _find_trailing_brace(text, paren_end + 1)
            if trailing is not None:
                return trailing
        return paren_end

    # ── Menu("Label") { ... } ─────────────────────────────────────────────
    if kind == "menu":
        paren_pos = text.find("(", match_start)
        if paren_pos == -1:
            return None
        paren_end = _safe_find_paren_end(text, paren_pos)
        if paren_end is None:
            return None
        trailing = _find_trailing_brace(text, paren_end + 1)
        if trailing is not None:
            return trailing
        return paren_end

    # ── NavigationLink variants ───────────────────────────────────────────
    if kind == "navlink_simple":
        paren_pos = text.find("(", match_start)
        if paren_pos == -1:
            return None
        paren_end = _safe_find_paren_end(text, paren_pos)
        if paren_end is None:
            return None
        trailing = _find_trailing_brace(text, paren_end + 1)
        if trailing is not None:
            return trailing
        return paren_end

    if kind == "navlink_dest":
        paren_pos = text.find("(", match_start)
        if paren_pos == -1:
            return None
        paren_end = _safe_find_paren_end(text, paren_pos)
        if paren_end is None:
            return None
        trailing = _find_trailing_brace(text, paren_end + 1)
        if trailing is not None:
            return trailing
        return paren_end

    if kind == "navlink_closure":
        brace_pos = match_end - 1
        if brace_pos < 0 or text[brace_pos] != "{":
            brace_pos = text.find("{", match_start, match_end)
            if brace_pos == -1:
                return None
        action_end = _safe_find_brace_end(text, brace_pos)
        if action_end is None:
            return None
        # Check for  label: { ... }  after the destination closure.
        lookahead = text[action_end + 1: min(n, action_end + 80)]
        m = re.match(r"\s*label\s*:\s*\{", lookahead)
        if m:
            label_brace_abs = action_end + 1 + m.end() - 1
            label_end = _safe_find_brace_end(text, label_brace_abs)
            if label_end is not None:
                return label_end
        return action_end

    # ── Text("...") with .onTapGesture ────────────────────────────────────
    if kind == "tappable_text":
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


def _sanitize_label(label: str) -> str:
    """Clean a raw label string before converting it to a disambiguator.

    Handles several real-world patterns that produce unreadable IDs:

    1. **Localization keys** (``auth.error.invalidCredentials``) → uses the
       last dot-segment (``invalidCredentials``).
    2. **String interpolation** (``@\\(author)``) → discarded entirely
       (returns empty so the caller falls back to numeric/binding).
    3. **Purely numeric** (``"45"``) → discarded (not a semantic label).
    4. **Special characters** stripped (``?``, ``!``, ``@``, etc.).
    """
    label = label.strip()
    if not label:
        return ""

    # Discard labels that contain Swift string interpolation \(…)
    if "\\(" in label or r"\(" in label:
        return ""

    # Discard purely numeric labels — not semantically meaningful.
    if label.isdigit():
        return ""

    # Localization key pattern: dotted identifiers like "auth.button.submit"
    # → use only the last segment ("submit").
    if "." in label and re.match(r'^[\w.]+$', label):
        label = label.rsplit(".", 1)[-1]

    # Strip special characters that don't belong in an identifier.
    label = re.sub(r'[?!@#$%^&*()+=\[\]{}<>|~/\\\'",;:]', '', label)

    return label.strip()


def _label_to_disambiguator(label: str) -> str:
    """Convert a human-readable label string to a camelCase disambiguator.

    The label is first sanitised (localisation keys shortened, interpolation
    and numeric-only labels discarded, special chars stripped) and then
    converted to camelCase.

    Examples::

        "Feed Type"                    -> "feedType"
        "Username"                     -> "username"
        "Sign In"                      -> "signIn"
        "submit"                       -> "submit"
        "auth.button.submit"           -> "submit"     (loc key → last segment)
        "feedback.button.submit"       -> "submit"
        "@\\(author)"                  -> ""            (interpolation → skip)
        "45"                           -> ""            (numeric → skip)
        "Forgot Password?"             -> "forgotPassword"
    """
    label = _sanitize_label(label)
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


def _extract_label_from_closure(text: str, closure_content: str) -> str:
    """Extract a meaningful label from a SwiftUI closure body.

    Tries, in order:
    1. Text("...") — literal text label
    2. Label("...", ...) — labeled content
    3. Image(systemName: "...") — SF Symbol mapped to semantic name

    Returns an empty string if no label can be extracted.
    """
    # 1. Text("Label")
    m = _TEXT_LABEL_RE.search(closure_content)
    if m:
        return m.group(1)

    # 2. Label("title", ...)
    m = _LABEL_RE.search(closure_content)
    if m:
        return m.group(1)

    # 3. Image(systemName: "sf.symbol") → mapped semantic name
    m = _IMAGE_SYSTEM_RE.search(closure_content)
    if m:
        symbol = m.group(1)
        return _SF_SYMBOL_LABELS.get(symbol, symbol.split(".")[-1])

    # 4. Image("assetName") — named asset image (not SF Symbol)
    m = _IMAGE_NAMED_RE.search(closure_content)
    if m:
        return m.group(1)

    return ""


def _find_foreach_variable(text: str, element_pos: int) -> str:
    """If the element at *element_pos* is inside a ForEach loop, return the
    loop variable name.  Returns empty string if not inside a ForEach.

    This enables generating interpolated IDs like:
        .accessibilityIdentifier("Screen_button_\\(item)")
    """
    # Search backwards from element_pos for the nearest ForEach
    # Look at up to 1000 chars before the element
    search_start = max(0, element_pos - 1000)
    search_region = text[search_start:element_pos]

    # Find the last ForEach match before our element
    last_match = None
    for m in _FOREACH_SIMPLE_RE.finditer(search_region):
        last_match = m

    if last_match is None:
        return ""

    # Verify the ForEach's brace scope actually contains our element
    # Find the opening brace of the ForEach closure
    foreach_abs_start = search_start + last_match.start()
    brace_search = text[foreach_abs_start:element_pos]
    brace_pos = brace_search.find("{")
    if brace_pos == -1:
        return ""

    abs_brace_pos = foreach_abs_start + brace_pos
    brace_end = _safe_find_brace_end(text, abs_brace_pos)
    if brace_end is None or brace_end < element_pos:
        return ""

    return last_match.group(1)


def _find_enclosing_struct(text: str, pos: int) -> Optional[str]:
    """Return the name of the ``struct X: View`` that encloses *pos*.

    Searches backwards from *pos* for the nearest ``struct … : View {``
    whose brace scope contains *pos*.  Returns ``None`` if no enclosing
    view struct can be determined (caller should fall back to file_stem).
    """
    best: Optional[str] = None
    for m in _STRUCT_VIEW_RE.finditer(text):
        if m.start() > pos:
            break
        brace_pos = text.find("{", m.end() - 1)
        if brace_pos == -1:
            continue
        brace_end = _safe_find_brace_end(text, brace_pos)
        if brace_end is not None and brace_end >= pos:
            best = m.group(1)
    return best


def _extract_binding_name(text: str, match_start: int, match_end: int) -> str:
    """Extract a ``$binding`` variable name from an element's parameter list.

    Looks for ``text: $foo``, ``value: $bar``, or ``selection: $baz`` in
    the parenthesised arguments of the element starting at *match_start*.
    Returns the binding name or empty string.
    """
    paren_pos = text.find("(", match_start, match_end + 200)
    if paren_pos == -1:
        return ""
    paren_end = _safe_find_paren_end(text, paren_pos)
    if paren_end is None:
        return ""
    params = text[paren_pos:paren_end + 1]
    m = _BINDING_RE.search(params)
    return m.group(1) if m else ""


def _has_on_tap_gesture(text: str, end_pos: int) -> bool:
    """Return True if ``.onTapGesture`` appears in the modifier chain
    immediately following *end_pos*."""
    window_end = min(len(text), end_pos + 1 + _A11Y_LOOK_AHEAD)
    window = text[end_pos + 1: window_end]
    stop = len(window)
    m = _NEW_ELEMENT_RE.search(window)
    if m:
        stop = m.start()
    return ".onTapGesture" in window[:stop]


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


# Matches auto-injected .accessibilityElement(true) that directly follows
# an auto-injected .accessibilityIdentifier line.
_AUTO_INJECTED_A11Y_ELEMENT_RE = re.compile(
    r'\n[ \t]*\.accessibilityElement\(true\)'
)


def strip_auto_injected_ids(source_text: str) -> str:
    """Remove all previously auto-injected ``.accessibilityIdentifier()`` lines.

    Only removes identifiers that match the auto-injection naming convention
    (``FileName_elementType_disambiguator``).  Manually authored identifiers
    are preserved.  Also strips associated ``.accessibilityElement(true)``
    lines that were injected alongside container elements.

    Returns the cleaned source text.
    """
    # Strip .accessibilityIdentifier lines first, then orphaned
    # .accessibilityElement(true) that directly followed them.
    result = _AUTO_INJECTED_A11Y_RE.sub("", source_text)
    # Only strip .accessibilityElement(true) if it's on its own line
    # (auto-injected pattern).  Manual ones won't be on a bare line.
    result = _AUTO_INJECTED_A11Y_ELEMENT_RE.sub("", result)
    return result


def inject_accessibility_ids(
    source_text: str, file_stem: str, *, force: bool = False,
    collected_ids: Optional[List[dict]] = None,
) -> str:
    """Inject ``.accessibilityIdentifier()`` modifiers into SwiftUI source.

    Only operates on files that contain a ``struct X: View`` declaration.
    Interactive elements that already have an ``.accessibilityIdentifier(``
    in their immediately following modifier chain are left untouched.

    When *force* is True, previously auto-injected identifiers are stripped
    first so that all elements are re-evaluated with the latest extraction
    logic.  Manually authored identifiers are never removed.

    Returns the (possibly modified) source text.  The original is returned
    unchanged when no injections are needed or when the file is not a SwiftUI
    view file.

    Naming convention: ``{StructName}_{elementType}_{disambiguator}``

    When the enclosing ``struct X: View`` can be determined, *StructName*
    is the struct name; otherwise it falls back to *file_stem*.

        * *elementType*: ``button``, ``textField``, ``secureField``,
          ``toggle``, ``tab``, ``navigationLink``, ``picker``, ``slider``,
          ``stepper``, ``datePicker``, ``menu``, ``link``, ``tappableText``
        * *disambiguator*: camelCase from the element label, ``$binding``
          variable name, or a numeric index when no label is available.

    Examples::

        LoginScreen_button_logOut          # from Button("Log Out")
        LoginScreen_textField_username     # from TextField("Username", ...)
        MainView_tab_settings              # from .tabItem { Image(systemName: "gear") }
        ProfileScreen_button_0             # fallback when no label extractable
        ListScreen_button_select_\\(item)  # inside ForEach
        SettingsScreen_picker_language     # from Picker("Language", ...)
        PlayerView_slider_volume           # from Slider(value: $volume)
    """
    # Guard: only process SwiftUI view files.
    if not SWIFTUI_VIEW_START_RE.search(source_text):
        return source_text

    # When force=True, strip old auto-injected IDs so they get re-generated.
    if force:
        source_text = strip_auto_injected_ids(source_text)

    # ── Collect candidate elements ───────────────────────────────────────────
    # Each entry: (start, match_end, element_type_name, internal_kind, label)
    candidates: List[Tuple[int, int, str, str, str]] = []

    for m in _BUTTON_SIMPLE_RE.finditer(source_text):
        candidates.append((m.start(), m.end(), "button", "button_simple", m.group(1)))

    for m in _BUTTON_ACTION_RE.finditer(source_text):
        # Extract label from the trailing label closure: Button(action: { }) { Text("Go") }
        label = ""
        paren_pos = source_text.find("(", m.start())
        if paren_pos != -1:
            paren_end = _safe_find_paren_end(source_text, paren_pos)
            if paren_end is not None:
                trailing_brace = _find_trailing_brace(source_text, paren_end + 1)
                if trailing_brace is not None:
                    brace_start = _skip_whitespace_forward(source_text, paren_end + 1)
                    closure_body = source_text[brace_start:trailing_brace + 1]
                    label = _extract_label_from_closure(source_text, closure_body)
        candidates.append((m.start(), m.end(), "button", "button_action", label))

    for m in _BUTTON_CLOSURE_RE.finditer(source_text):
        # Extract label from label: { } closure: Button { ... } label: { Text("Go") }
        label = ""
        brace_pos = m.end() - 1
        action_end = _safe_find_brace_end(source_text, brace_pos)
        if action_end is not None:
            lookahead = source_text[action_end + 1: min(len(source_text), action_end + 80)]
            lm = re.match(r"\s*label\s*:\s*\{", lookahead)
            if lm:
                label_brace_abs = action_end + 1 + lm.end() - 1
                label_end = _safe_find_brace_end(source_text, label_brace_abs)
                if label_end is not None:
                    closure_body = source_text[label_brace_abs:label_end + 1]
                    label = _extract_label_from_closure(source_text, closure_body)
        candidates.append((m.start(), m.end(), "button", "button_closure", label))

    for m in _TEXTFIELD_RE.finditer(source_text):
        etype = "textField" if m.group(1) == "TextField" else "secureField"
        candidates.append((m.start(), m.end(), etype, "field", m.group(2)))

    for m in _TOGGLE_RE.finditer(source_text):
        candidates.append((m.start(), m.end(), "toggle", "toggle", m.group(1)))

    for m in _TABITEM_RE.finditer(source_text):
        # Try to extract label from the .tabItem { } block content.
        brace_pos = m.end() - 1  # position of opening '{'
        tab_label = ""
        block_end = _safe_find_brace_end(source_text, brace_pos)
        if block_end is not None:
            block_content = source_text[brace_pos: block_end + 1]
            tab_label = _extract_label_from_closure(source_text, block_content)
        candidates.append((m.start(), m.end(), "tab", "tabitem", tab_label))

    # ── NavigationLink ────────────────────────────────────────────────────
    for m in _NAVLINK_SIMPLE_RE.finditer(source_text):
        candidates.append((m.start(), m.end(), "navigationLink", "navlink_simple", m.group(1)))

    for m in _NAVLINK_DEST_RE.finditer(source_text):
        label = ""
        paren_pos = source_text.find("(", m.start())
        if paren_pos != -1:
            paren_end = _safe_find_paren_end(source_text, paren_pos)
            if paren_end is not None:
                trailing_brace = _find_trailing_brace(source_text, paren_end + 1)
                if trailing_brace is not None:
                    brace_start = _skip_whitespace_forward(source_text, paren_end + 1)
                    closure_body = source_text[brace_start:trailing_brace + 1]
                    label = _extract_label_from_closure(source_text, closure_body)
        candidates.append((m.start(), m.end(), "navigationLink", "navlink_dest", label))

    for m in _NAVLINK_CLOSURE_RE.finditer(source_text):
        label = ""
        brace_pos = m.end() - 1
        action_end = _safe_find_brace_end(source_text, brace_pos)
        if action_end is not None:
            lookahead = source_text[action_end + 1: min(len(source_text), action_end + 80)]
            lm = re.match(r"\s*label\s*:\s*\{", lookahead)
            if lm:
                label_brace_abs = action_end + 1 + lm.end() - 1
                label_end = _safe_find_brace_end(source_text, label_brace_abs)
                if label_end is not None:
                    closure_body = source_text[label_brace_abs:label_end + 1]
                    label = _extract_label_from_closure(source_text, closure_body)
        candidates.append((m.start(), m.end(), "navigationLink", "navlink_closure", label))

    # ── Picker ────────────────────────────────────────────────────────────
    for m in _PICKER_RE.finditer(source_text):
        candidates.append((m.start(), m.end(), "picker", "picker", m.group(1)))

    # ── Slider ────────────────────────────────────────────────────────────
    for m in _SLIDER_RE.finditer(source_text):
        # Slider has no string label; use $binding name as disambiguator.
        binding = _extract_binding_name(source_text, m.start(), m.end())
        candidates.append((m.start(), m.end(), "slider", "slider", binding))

    # ── Stepper ───────────────────────────────────────────────────────────
    for m in _STEPPER_RE.finditer(source_text):
        candidates.append((m.start(), m.end(), "stepper", "stepper", m.group(1)))

    # ── DatePicker ────────────────────────────────────────────────────────
    for m in _DATEPICKER_RE.finditer(source_text):
        candidates.append((m.start(), m.end(), "datePicker", "datepicker", m.group(1)))

    # ── Menu ──────────────────────────────────────────────────────────────
    for m in _MENU_RE.finditer(source_text):
        candidates.append((m.start(), m.end(), "menu", "menu", m.group(1)))

    # ── Link ──────────────────────────────────────────────────────────────
    for m in _LINK_RE.finditer(source_text):
        candidates.append((m.start(), m.end(), "link", "link", m.group(1)))

    # ── Text("...") with .onTapGesture — tappable text ───────────────────
    for m in _TEXT_TAP_RE.finditer(source_text):
        # Only include if followed by .onTapGesture in the modifier chain.
        # We need to find the end of Text(...) first to check modifiers.
        paren_pos = source_text.find("(", m.start())
        if paren_pos == -1:
            continue
        paren_end = _safe_find_paren_end(source_text, paren_pos)
        if paren_end is None:
            continue
        if _has_on_tap_gesture(source_text, paren_end):
            candidates.append((m.start(), m.end(), "tappableText", "tappable_text", m.group(1)))

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

        # Fallback: try $binding variable name when no label is available.
        if not raw_disambiguator:
            binding = _extract_binding_name(source_text, start, match_end)
            if binding:
                raw_disambiguator = binding

        # Check if element is inside a ForEach loop
        foreach_var = _find_foreach_variable(source_text, start)

        if raw_disambiguator:
            # Resolve collisions by appending _N suffix for readability.
            if raw_disambiguator not in type_labels_seen[etype]:
                disambiguator = raw_disambiguator
            else:
                disambiguator = f"{raw_disambiguator}_{type_index[etype]}"
            type_labels_seen[etype].add(raw_disambiguator)  # track the base name
        else:
            # Numeric fallback: FeedScreen_button_0
            disambiguator = str(type_index[etype])

        type_index[etype] += 1

        # Use enclosing struct name when available; fall back to file_stem.
        struct_name = _find_enclosing_struct(source_text, start) or file_stem

        # Match the indentation of the element's own line.
        indent = _get_line_indent(source_text, start)

        if foreach_var:
            # Use string interpolation for ForEach elements so each
            # iteration gets a unique, runtime-derived ID.
            a11y_id = f"{struct_name}_{etype}_{disambiguator}_\\({foreach_var})"
            injection_text = f'\n{indent}.accessibilityIdentifier("{a11y_id}")'
        else:
            a11y_id = f"{struct_name}_{etype}_{disambiguator}"
            injection_text = f'\n{indent}.accessibilityIdentifier("{a11y_id}")'

        # Container-like elements need .accessibilityElement(true) to be
        # discoverable by XCUITest (mirrors UIKit runtime behaviour for
        # UITableViewCell / UICollectionViewCell / UISwitch).
        if etype in _CONTAINER_ELEMENT_TYPES:
            injection_text += f"\n{indent}.accessibilityElement(true)"

        # Collect for debugging / JSON export
        if collected_ids is not None:
            line_no = source_text[:start].count("\n") + 1
            collected_ids.append({
                "id": a11y_id,
                "file": file_stem,
                "element_type": etype,
                "label": label or None,
                "line": line_no,
                "foreach_var": foreach_var or None,
            })

        injections.append((end_pos, injection_text))

    if not injections:
        return source_text

    # ── Apply injections back-to-front so earlier offsets stay valid ─────────
    result = source_text
    for end_pos, inj in sorted(injections, key=lambda x: x[0], reverse=True):
        result = result[: end_pos + 1] + inj + result[end_pos + 1:]

    return result


def inject_directory(
    root: Path,
    exclude_dirs: Optional[Set[str]] = None,
    *,
    force: bool = False,
) -> Dict[str, str]:
    """Walk *root* for ``.swift`` files and inject accessibility IDs in-place.

    Files are only modified when:
    * They end with ``.swift``.
    * They are not inside any directory listed in *exclude_dirs*.
    * They contain the string ``'View'`` (quick pre-filter).
    * :func:`inject_accessibility_ids` actually changes them.

    When *force* is True, previously auto-injected identifiers are stripped
    and re-generated with the latest extraction logic.

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
    force:
        When True, strip old auto-injected IDs before re-injecting.
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

            modified = inject_accessibility_ids(original, fpath.stem, force=force)

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
