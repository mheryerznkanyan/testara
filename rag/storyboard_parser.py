"""
rag/storyboard_parser.py

Parse .storyboard and .xib files (XML) to extract accessibilityIdentifier
attributes and map them to their associated ViewController classes.

Usage::

    from rag.storyboard_parser import extract_storyboard_ids

    ids = extract_storyboard_ids("Login.storyboard")
    # {"LoginViewController": ["emailField", "passwordField", "loginButton"]}
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional


# ─── ViewController container tag names ─────────────────────────────────────

_VC_TAGS: frozenset[str] = frozenset({
    "viewController",
    "tableViewController",
    "collectionViewController",
    "navigationController",
    "tabBarController",
    "pageViewController",
    "splitViewController",
    "hostingController",
})

# XIB files use a flat <objects> root; the first VC-like object is the owner
_XIB_OWNER_TAGS: frozenset[str] = frozenset({
    "placeholder",  # <placeholder placeholderIdentifier="IBFilesOwner" customClass="...">
})


# ─── Public API ─────────────────────────────────────────────────────────────

def extract_storyboard_ids(storyboard_path: str) -> Dict[str, List[str]]:
    """Parse a .storyboard or .xib file and return accessibility IDs per VC.

    Args:
        storyboard_path: Absolute or relative path to a ``.storyboard`` or
            ``.xib`` file.

    Returns:
        A dict mapping ViewController class names to their accessibility
        identifier strings, e.g.::

            {
                "LoginViewController": ["emailField", "passwordField", "loginButton"],
                "_unassigned": ["someFloatingLabel"],
            }

        Elements that cannot be attributed to any ViewController are placed
        under the key ``"_unassigned"``.

    Raises:
        FileNotFoundError: If *storyboard_path* does not exist.
        OSError: If the file cannot be opened for reading.
        ValueError: If the XML is malformed / unparseable.
    """
    path = Path(storyboard_path)

    if not path.exists():
        raise FileNotFoundError(f"Storyboard file not found: {storyboard_path}")

    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise OSError(f"Cannot read {storyboard_path}: {exc}") from exc

    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise ValueError(f"Malformed XML in '{path.name}': {exc}") from exc

    result: Dict[str, List[str]] = {}
    is_xib = path.suffix.lower() == ".xib"

    if is_xib:
        # XIB files: find the Files Owner placeholder first to get the class name
        xib_owner = _find_xib_owner(root)
        _walk_element(root, current_vc=xib_owner, result=result)
    else:
        # Storyboard: multiple scenes, each with its own VC
        _walk_element(root, current_vc=None, result=result)

    # Deduplicate while preserving insertion order
    return {vc: list(dict.fromkeys(ids)) for vc, ids in result.items() if ids}


# ─── Internals ───────────────────────────────────────────────────────────────

def _find_xib_owner(root: ET.Element) -> Optional[str]:
    """Return the customClass of the XIB's File's Owner placeholder, if any."""
    for elem in root.iter():
        if elem.tag in _XIB_OWNER_TAGS:
            placeholder_id = elem.get("placeholderIdentifier", "")
            if "IBFilesOwner" in placeholder_id or "filesOwner" in placeholder_id.lower():
                custom_class = elem.get("customClass")
                if custom_class:
                    return custom_class
    return None


def _resolve_vc_class(element: ET.Element) -> Optional[str]:
    """Return the ViewController class name if *element* is a VC container."""
    if element.tag in _VC_TAGS:
        custom_class = element.get("customClass")
        if custom_class:
            return custom_class
        # Fall back to the storyboard ID so the entry isn't lost
        storyboard_id = element.get("storyboardIdentifier") or element.get("id")
        if storyboard_id:
            return storyboard_id
    return None


def _walk_element(
    element: ET.Element,
    current_vc: Optional[str],
    result: Dict[str, List[str]],
) -> None:
    """Recursively walk XML tree, tracking VC scope and collecting a11y IDs."""
    # Check if this element opens a new ViewController scope
    vc_class = _resolve_vc_class(element)
    if vc_class:
        current_vc = vc_class

    # Collect accessibilityIdentifier on this element
    a11y_id = element.get("accessibilityIdentifier", "").strip()
    if a11y_id:
        scope = current_vc or "_unassigned"
        result.setdefault(scope, []).append(a11y_id)

    # Recurse
    for child in element:
        _walk_element(child, current_vc, result)
