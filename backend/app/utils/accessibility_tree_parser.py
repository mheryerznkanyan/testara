from dataclasses import dataclass, field
from typing import List
import json as _json
import logging
from pathlib import Path
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

# Short type codes for compressed output
_TYPE_SHORT = {
    "XCUIElementTypeButton": "B",
    "XCUIElementTypeStaticText": "T",
    "XCUIElementTypeTextField": "In",
    "XCUIElementTypeSecureTextField": "Pw",
    "XCUIElementTypeCell": "C",
    "XCUIElementTypeImage": "Img",
    "XCUIElementTypeSwitch": "Sw",
    "XCUIElementTypeSlider": "Sl",
    "XCUIElementTypeSearchField": "SF",
    "XCUIElementTypeSegmentedControl": "Seg",
    "XCUIElementTypeTab": "Tab",
    "XCUIElementTypeLink": "Lnk",
    "XCUIElementTypeNavigationBar": "Nav",
    "XCUIElementTypeTabBar": "TBar",
    "XCUIElementTypeTable": "Tbl",
    "XCUIElementTypeOther": "O",
}

_NOISE_PATTERNS = frozenset({
    "scroll bar", "horizontal scroll", "vertical scroll",
    "separator", "dimming", "debug", "additionaldimming",
})

INTERACTIVE_TYPES = {
    "XCUIElementTypeButton",
    "XCUIElementTypeTextField",
    "XCUIElementTypeSecureTextField",
    "XCUIElementTypeSwitch",
    "XCUIElementTypeSlider",
    "XCUIElementTypeSegmentedControl",
    "XCUIElementTypeTab",
    "XCUIElementTypeLink",
    "XCUIElementTypeSearchField",
    "XCUIElementTypeCell",
    "XCUIElementTypeStaticText",
    "XCUIElementTypeImage",
}


@dataclass
class ElementInfo:
    element_type: str        # e.g. XCUIElementTypeButton
    name: str                # = .accessibilityIdentifier (THE key)
    label: str               # = visible text (localization resolved)
    value: str               # = current content/value
    enabled: bool
    visible: bool
    x: int
    y: int
    width: int
    height: int

    @property
    def short_type(self) -> str:
        """XCUIElementTypeButton -> Button"""
        return self.element_type.replace("XCUIElementType", "")

    @property
    def is_interactive(self) -> bool:
        return self.element_type in INTERACTIVE_TYPES

    @property
    def has_useful_name(self) -> bool:
        """True if name is non-empty and not just the element type"""
        return bool(self.name) and self.name != self.element_type


@dataclass
class AccessibilitySnapshot:
    elements: List[ElementInfo] = field(default_factory=list)
    screenshot_b64: str = ""
    raw_xml: str = ""
    bundle_id: str = ""
    device_udid: str = ""

    def interactive_elements(self) -> List[ElementInfo]:
        return [e for e in self.elements if e.is_interactive and e.has_useful_name]

    def to_context_string(self) -> str:
        """Format for LLM — concise, actionable."""
        interactive = self.interactive_elements()
        if not interactive:
            return "RUNTIME ACCESSIBILITY TREE: No interactive elements with identifiers found."

        lines = [
            "RUNTIME ACCESSIBILITY TREE (live from running app — highest confidence):",
            "Rule: use 'name' values directly in XCUITest — app.buttons[\"name\"], app.textFields[\"name\"]",
            "",
        ]
        for e in interactive:
            parts = [f"  [{e.short_type:<16}]  name={e.name!r:<35} label={e.label!r}"]
            if e.value and e.value != e.label:
                parts[0] += f"  value={e.value!r}"
            lines.append(parts[0])
        return "\n".join(lines)


def parse_wda_xml(xml_string: str) -> List[ElementInfo]:
    """Parse WebDriverAgent page_source XML into ElementInfo list."""
    elements = []
    try:
        root = ET.fromstring(xml_string)
        _walk(root, elements)
    except ET.ParseError:
        pass
    return elements


def _walk(node: ET.Element, result: List[ElementInfo]) -> None:
    """Recursively walk XML tree collecting elements."""
    try:
        frame_x = int(node.get("x", 0))
        frame_y = int(node.get("y", 0))
        frame_w = int(node.get("width", 0))
        frame_h = int(node.get("height", 0))

        elem = ElementInfo(
            element_type=node.tag,
            name=node.get("name", "") or "",
            label=node.get("label", "") or "",
            value=node.get("value", "") or "",
            enabled=node.get("enabled", "false").lower() == "true",
            visible=node.get("visible", "false").lower() == "true",
            x=frame_x, y=frame_y,
            width=frame_w, height=frame_h,
        )
        result.append(elem)
    except (ValueError, AttributeError):
        pass

    for child in node:
        _walk(child, result)


def filter_interactive(elements: List[ElementInfo]) -> List[ElementInfo]:
    return [e for e in elements if e.is_interactive and e.has_useful_name and e.visible]


def _compress_elements(elements: List[ElementInfo]) -> tuple:
    """Compress element list: deduplicate, remove noise, fuzzy dedup.

    Returns (unique_elements, counts_dict) where counts_dict maps
    (element_type, name) -> occurrence count.
    """
    # 1. Remove images with no name AND no label
    elements = [e for e in elements if not (
        e.element_type == "XCUIElementTypeImage" and not e.name and not e.label
    )]

    # 2. Remove noise elements
    elements = [e for e in elements if not any(
        n in e.name.lower() for n in _NOISE_PATTERNS
    )]

    # 3. Remove StaticText duplicating Button/Cell names (fuzzy match)
    button_names = {
        e.name.strip().lower() for e in elements
        if e.element_type in ("XCUIElementTypeButton", "XCUIElementTypeCell")
        and e.name
    }
    elements = [e for e in elements if not (
        e.element_type == "XCUIElementTypeStaticText"
        and e.name.strip().lower() in button_names
    )]

    # 4. Sort deterministically: by type then name (cache-stable)
    elements.sort(key=lambda e: (e.element_type, e.name))

    # 5. Deduplicate: count occurrences, keep first
    seen: dict = {}
    unique: list = []
    for e in elements:
        key = (e.element_type, e.name)
        if key in seen:
            seen[key] += 1
        else:
            seen[key] = 1
            unique.append(e)

    return unique, seen


def _format_compressed_line(e: ElementInfo, count: int = 1) -> str:
    """Format a single element as a compressed line."""
    short_type = _TYPE_SHORT.get(e.element_type, e.short_type)
    parts = f"  [{short_type:<3}] \"{e.name}\""
    if e.value and e.value != e.label and e.value != e.name:
        parts += f"  value='{e.value}'"
    if count > 3:
        parts += f"  (×{count})"
    return parts


@dataclass
class ScreenCapture:
    """A single screen's accessibility snapshot with navigation context."""
    screen_label: str  # e.g. "Home", "Search", "Search > Category"
    elements: List[ElementInfo] = field(default_factory=list)
    screenshot_b64: str = ""
    navigation_path: str = ""  # how to get here, e.g. "tap 'Search' tab"

    def interactive_elements(self) -> List[ElementInfo]:
        return [e for e in self.elements if e.is_interactive and e.has_useful_name]


@dataclass
class MultiScreenSnapshot:
    """Collection of accessibility snapshots from multiple screens."""
    screens: List[ScreenCapture] = field(default_factory=list)
    bundle_id: str = ""
    device_udid: str = ""

    def all_interactive_elements(self) -> List[ElementInfo]:
        """Deduplicated interactive elements across all screens."""
        seen = set()
        result = []
        for screen in self.screens:
            for e in screen.interactive_elements():
                key = (e.element_type, e.name)
                if key not in seen:
                    seen.add(key)
                    result.append(e)
        return result

    def interactive_elements(self) -> List[ElementInfo]:
        """Alias for compatibility with AccessibilitySnapshot."""
        return self.all_interactive_elements()

    def to_context_string(self) -> str:
        """Format all screens for LLM context — compressed, deduplicated, and deterministic."""
        if not self.screens:
            return "RUNTIME ACCESSIBILITY TREE: No screens captured."

        lines: list = []

        # Deduplicate screens with identical element sets
        seen_fingerprints: dict = {}  # fingerprint → (label, nav_path)
        unique_screens = []

        for screen in self.screens:
            interactive = screen.interactive_elements()
            if not interactive:
                continue
            # Fingerprint = sorted set of (type, name) tuples
            fingerprint = tuple(sorted({(e.element_type, e.name) for e in interactive if e.name}))
            if fingerprint in seen_fingerprints:
                # Duplicate screen — note it but don't add again
                continue
            seen_fingerprints[fingerprint] = (screen.screen_label, screen.navigation_path)
            unique_screens.append(screen)

        for screen in unique_screens:
            interactive = screen.interactive_elements()
            compressed, counts = _compress_elements(interactive)
            if not compressed:
                continue

            nav_hint = f"  (navigation: {screen.navigation_path})" if screen.navigation_path else ""
            lines.append(f"── SCREEN: {screen.screen_label}{nav_hint} ──")

            for e in compressed:
                count = counts.get((e.element_type, e.name), 1)
                lines.append(_format_compressed_line(e, count))
            lines.append("")

        return "\n".join(lines)

    def save(self, path: str) -> None:
        """Save snapshot to JSON file (excludes screenshots to save space)."""
        data = {
            "bundle_id": self.bundle_id,
            "device_udid": self.device_udid,
            "screens": [
                {
                    "screen_label": s.screen_label,
                    "navigation_path": s.navigation_path,
                    "elements": [
                        {
                            "element_type": e.element_type,
                            "name": e.name,
                            "label": e.label,
                            "value": e.value,
                            "enabled": e.enabled,
                            "visible": e.visible,
                            "x": e.x, "y": e.y,
                            "width": e.width, "height": e.height,
                        }
                        for e in s.elements
                    ],
                }
                for s in self.screens
            ],
        }
        Path(path).write_text(_json.dumps(data, indent=2))
        logger.info("Saved multi-screen snapshot to %s (%d screens)", path, len(self.screens))

    @classmethod
    def load(cls, path: str) -> "MultiScreenSnapshot":
        """Load snapshot from JSON file."""
        text = Path(path).read_text()
        data = _json.loads(text)
        screens = []
        for s in data.get("screens", []):
            elements = [
                ElementInfo(
                    element_type=e["element_type"],
                    name=e["name"],
                    label=e["label"],
                    value=e.get("value", ""),
                    enabled=e.get("enabled", True),
                    visible=e.get("visible", True),
                    x=e.get("x", 0), y=e.get("y", 0),
                    width=e.get("width", 0), height=e.get("height", 0),
                )
                for e in s.get("elements", [])
            ]
            screens.append(ScreenCapture(
                screen_label=s["screen_label"],
                elements=elements,
                navigation_path=s.get("navigation_path", ""),
            ))
        snapshot = cls(
            screens=screens,
            bundle_id=data.get("bundle_id", ""),
            device_udid=data.get("device_udid", ""),
        )
        logger.info("Loaded multi-screen snapshot from %s (%d screens)", path, len(screens))
        return snapshot
