from dataclasses import dataclass, field
from typing import List, Optional
import xml.etree.ElementTree as ET

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


@dataclass
class ScreenCapture:
    """A single screen's accessibility snapshot with metadata."""
    screen_name: str
    snapshot: AccessibilitySnapshot
    is_target: bool = False


@dataclass
class MultiScreenSnapshot:
    """Accessibility snapshots from multiple screens along a navigation path."""
    screens: List[ScreenCapture] = field(default_factory=list)
    navigation_path: List[str] = field(default_factory=list)
    bundle_id: str = ""
    device_udid: str = ""

    @property
    def target_snapshot(self) -> Optional[AccessibilitySnapshot]:
        for sc in self.screens:
            if sc.is_target:
                return sc.snapshot
        return self.screens[-1].snapshot if self.screens else None

    def interactive_elements(self) -> List[ElementInfo]:
        target = self.target_snapshot
        return target.interactive_elements() if target else []

    def to_context_string(self) -> str:
        """Format all screens for LLM prompt, with navigation order and target marked."""
        if not self.screens:
            return "RUNTIME ACCESSIBILITY TREE: No screens captured."

        lines = [
            "RUNTIME ACCESSIBILITY TREE (live from running app — highest confidence):",
            "Rule: use 'name' values directly in XCUITest — app.buttons[\"name\"], app.textFields[\"name\"]",
            f"Navigation path: {' -> '.join(self.navigation_path)}" if self.navigation_path else "",
            "",
        ]

        for sc in self.screens:
            marker = " [TARGET SCREEN]" if sc.is_target else ""
            lines.append(f"--- Screen: {sc.screen_name}{marker} ---")
            interactive = sc.snapshot.interactive_elements()
            if not interactive:
                lines.append("  (no interactive elements with identifiers)")
            else:
                for e in interactive:
                    parts = f"  [{e.short_type:<16}]  name={e.name!r:<35} label={e.label!r}"
                    if e.value and e.value != e.label:
                        parts += f"  value={e.value!r}"
                    lines.append(parts)
            lines.append("")

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
