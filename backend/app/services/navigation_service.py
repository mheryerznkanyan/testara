"""Lightweight navigation context extractor for iOS apps.

Scans Swift source files with regex to detect:
- Screens (SwiftUI Views, UIViewControllers)
- Navigation patterns (NavigationLink, sheet, push, present)
- Entry point and screen reachability

No tree-sitter dependency — pure regex-based extraction.
"""

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# SwiftUI View structs: struct FooView: View {
_SWIFTUI_VIEW_RE = re.compile(
    r"struct\s+(\w+)\s*:\s*(?:\w+,\s*)*View\b", re.MULTILINE
)

# UIKit view controllers: class FooViewController: UIViewController {
_UIKIT_VC_RE = re.compile(
    r"class\s+(\w+)\s*:\s*(?:\w+,\s*)*UI\w*ViewController\b", re.MULTILINE
)

# SwiftUI navigation patterns
_NAV_LINK_RE = re.compile(r"NavigationLink\s*\(", re.MULTILINE)
_SHEET_RE = re.compile(r"\.sheet\s*\(", re.MULTILINE)
_FULLSCREEN_RE = re.compile(r"\.fullScreenCover\s*\(", re.MULTILINE)
_NAV_DEST_RE = re.compile(r"\.navigationDestination\s*\(", re.MULTILINE)

# SwiftUI TabView — destination views listed inside TabView { ... }
_TAB_VIEW_RE = re.compile(r"TabView\s*(?:\([^)]*\))?\s*\{", re.MULTILINE)

# UIKit navigation patterns
_PUSH_VC_RE = re.compile(r"pushViewController\s*\(", re.MULTILINE)
_PRESENT_RE = re.compile(r"(?<!override\s)present\s*\(\s*\w+", re.MULTILINE)
_PERFORM_SEGUE_RE = re.compile(r"performSegue\s*\(", re.MULTILINE)

# Destination extraction — best-effort: SomeView() or SomeViewController()
_DESTINATION_RE = re.compile(r"(\w+(?:View|Controller|Screen))\s*\(")

# Accessibility identifiers
_ACCESSIBILITY_ID_RE = re.compile(
    r'\.accessibilityIdentifier\s*\(\s*"([^"]+)"\s*\)', re.MULTILINE
)


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------

class _Screen:
    __slots__ = ("name", "file_path", "screen_type", "line_number")

    def __init__(self, name: str, file_path: str, screen_type: str, line_number: int):
        self.name = name
        self.file_path = file_path
        self.screen_type = screen_type
        self.line_number = line_number


class _NavAction:
    __slots__ = ("source", "destination", "method", "line_number")

    def __init__(self, source: str, destination: Optional[str], method: str, line_number: int):
        self.source = source
        self.destination = destination
        self.method = method
        self.line_number = line_number


# ---------------------------------------------------------------------------
# Main service
# ---------------------------------------------------------------------------

class NavigationService:
    """Extract and format navigation context from an iOS project directory."""

    def __init__(self, app_path: str):
        self._app_path = Path(app_path)
        self._screens: List[_Screen] = []
        self._actions: List[_NavAction] = []
        self._entry_point: Optional[str] = None
        self._login_is_entry = False
        self._extracted = False

    # ---- public API --------------------------------------------------------

    def extract(self) -> None:
        """Scan Swift files and populate screens + navigation actions."""
        if not self._app_path.exists():
            logger.warning("App path does not exist: %s", self._app_path)
            return

        swift_files = sorted(self._app_path.rglob("*.swift"))
        swift_files = [
            f for f in swift_files
            if not any(
                part in f.parts
                for part in ("build", ".build", "DerivedData", "Pods", ".swiftpm")
            )
            and "Tests" not in f.name
            and "Test" not in f.name
        ]

        for sf in swift_files:
            try:
                source = sf.read_text(errors="replace")
            except Exception:
                continue
            rel = str(sf.relative_to(self._app_path))
            self._extract_screens(source, rel)
            self._extract_actions(source, rel)

        # Determine entry point
        self._entry_point = self._guess_entry_point(swift_files)
        self._extracted = True
        logger.info(
            "Navigation extraction done: %d screens, %d actions, entry=%s",
            len(self._screens), len(self._actions), self._entry_point,
        )

    def format_for_prompt(self, test_description: str) -> str:
        """Return a formatted navigation context string for LLM prompt injection.

        Returns empty string if nothing relevant is found.
        """
        if not self._extracted:
            self.extract()

        if not self._screens:
            return ""

        desc_lower = test_description.lower()

        # Find relevant screens mentioned in description
        relevant: List[_Screen] = []
        for s in self._screens:
            base = s.name.replace("View", "").replace("Controller", "").replace("Screen", "").lower()
            if base in desc_lower or s.name.lower() in desc_lower:
                relevant.append(s)

        entry_is_login = self._login_is_entry or (
            self._entry_point and "login" in self._entry_point.lower()
        )

        if not relevant and not entry_is_login:
            # Still provide overview if we have screens
            if not self._screens:
                return ""

        lines: List[str] = []
        lines.append("## NAVIGATION CONTEXT (use this to understand app flow):")
        lines.append("")

        # App overview
        app_name = self._app_path.name
        lines.append(f"App: {app_name}")
        lines.append(f"Total Screens: {len(self._screens)}")
        lines.append(f"Entry Point: {self._entry_point or 'unknown'}")
        lines.append("")

        # All screens
        lines.append("**All screens in the app:**")
        for s in self._screens:
            lines.append(f"- {s.name} ({s.screen_type}) — {s.file_path}:{s.line_number}")
        lines.append("")

        # Relevant screens
        if relevant:
            lines.append("**Screens involved in this test:**")
            for s in relevant:
                lines.append(f"- {s.name} ({s.screen_type}) — {s.file_path}:{s.line_number}")
            lines.append("")

        # Navigation paths to relevant screens
        if relevant and self._actions:
            lines.append("**How to reach these screens:**")
            reachability = self._build_reachability()
            for s in relevant:
                path = reachability.get(s.name)
                if path:
                    lines.append(f"- To reach {s.name}: {' -> '.join(path)}")
                    if any("login" in step.lower() for step in path):
                        lines.append(f"  !! IMPORTANT: This screen requires login first")
            lines.append("")

        # Navigation actions summary
        if self._actions:
            lines.append("**Navigation actions:**")
            for a in self._actions:
                dest = a.destination or "?"
                lines.append(f"- {a.source} --[{a.method}]--> {dest}")
            lines.append("")

        # Login prerequisites
        if entry_is_login:
            from app.core.config import settings
            lines.append("**Test Setup Requirements:**")
            lines.append("- App starts at login screen")
            lines.append("- Most features require login first")
            lines.append("- CRITICAL: You MUST include login steps at the START of every test before navigating to other screens")
            if settings.test_credentials_email and settings.test_credentials_password:
                lines.append(f"- Login credentials to use: email=\"{settings.test_credentials_email}\", password=\"{settings.test_credentials_password}\"")
                lines.append("- Login steps: tap email field, type email, tap password field, type password, tap login button")
            lines.append("")

        # Instructions
        lines.append("**Instructions for test generation:**")
        lines.append("1. Use this navigation context to understand prerequisites (e.g., login)")
        lines.append("2. Add navigation steps automatically (don't expect user to specify them)")
        lines.append("3. Generate complete test including all necessary navigation to reach the target screen")
        lines.append("")

        return "\n".join(lines)

    def get_navigation_path(self, test_description: str) -> dict:
        """Return structured navigation data for programmatic use.

        Returns:
            {
                "entry_point": "ContentView",
                "target_screens": [
                    {"name": "SettingsView", "path": ["ContentView", "HomeView", "SettingsView"]}
                ],
            }
        """
        if not self._extracted:
            self.extract()

        desc_lower = test_description.lower()

        # Find relevant screens mentioned in description
        relevant: List[_Screen] = []
        for s in self._screens:
            base = s.name.replace("View", "").replace("Controller", "").replace("Screen", "").lower()
            if base in desc_lower or s.name.lower() in desc_lower:
                relevant.append(s)

        reachability = self._build_reachability()

        targets = []
        for s in relevant:
            path = reachability.get(s.name)
            if not path and self._entry_point and s.name != self._entry_point:
                # BFS couldn't find a path (e.g. TabView navigation not detected),
                # but we know the entry point — provide [entry, target] so Appium
                # at least attempts navigation via element matching.
                path = [self._entry_point, s.name]
            elif not path:
                path = [s.name]
            targets.append({"name": s.name, "path": path})

        return {
            "entry_point": self._entry_point,
            "target_screens": targets,
        }

    # ---- private helpers ---------------------------------------------------

    def _extract_screens(self, source: str, rel_path: str) -> None:
        for m in _SWIFTUI_VIEW_RE.finditer(source):
            name = m.group(1)
            line = source[: m.start()].count("\n") + 1
            self._screens.append(_Screen(name, rel_path, "SwiftUI View", line))

        for m in _UIKIT_VC_RE.finditer(source):
            name = m.group(1)
            line = source[: m.start()].count("\n") + 1
            self._screens.append(_Screen(name, rel_path, "UIViewController", line))

    def _extract_actions(self, source: str, rel_path: str) -> None:
        # Determine which screen this file belongs to
        screen_name = self._screen_for_file(rel_path)
        if not screen_name:
            # Try from filename
            stem = Path(rel_path).stem
            screen_name = stem

        patterns = [
            (_NAV_LINK_RE, "NavigationLink"),
            (_SHEET_RE, "sheet"),
            (_FULLSCREEN_RE, "fullScreenCover"),
            (_NAV_DEST_RE, "navigationDestination"),
            (_PUSH_VC_RE, "pushViewController"),
            (_PRESENT_RE, "present"),
            (_PERFORM_SEGUE_RE, "performSegue"),
        ]

        for regex, method in patterns:
            for m in regex.finditer(source):
                line = source[: m.start()].count("\n") + 1
                # Try to find destination in surrounding context
                context = source[m.start(): m.start() + 300]
                dest_m = _DESTINATION_RE.search(context)
                dest = dest_m.group(1) if dest_m else None
                self._actions.append(_NavAction(screen_name, dest, method, line))

        # TabView: extract all destination views inside the TabView body
        for m in _TAB_VIEW_RE.finditer(source):
            # Grab a larger context window to capture all tab destinations
            context = source[m.start(): m.start() + 2000]
            line = source[: m.start()].count("\n") + 1
            for dest_m in _DESTINATION_RE.finditer(context):
                dest = dest_m.group(1)
                if dest != screen_name:  # avoid self-reference
                    self._actions.append(_NavAction(screen_name, dest, "TabView", line))

    def _screen_for_file(self, rel_path: str) -> Optional[str]:
        for s in self._screens:
            if s.file_path == rel_path:
                return s.name
        return None

    def _guess_entry_point(self, swift_files: List[Path]) -> Optional[str]:
        """Find the entry point by looking for @main or ContentView.

        Also detects conditional login patterns like:
            if authService.isAuthenticated { MainView() } else { LoginView() }
        """
        root_view: Optional[str] = None

        for sf in swift_files:
            try:
                source = sf.read_text(errors="replace")
            except Exception:
                continue
            if "@main" in source:
                wg = re.search(r"WindowGroup\s*\{[^}]*?(\w+View)\s*\(", source, re.DOTALL)
                if wg:
                    root_view = wg.group(1)
                    break

        # If root view is a wrapper (ContentView), check if it conditionally
        # shows a LoginView — that means the actual initial screen is LoginView
        if root_view:
            for sf in swift_files:
                try:
                    source = sf.read_text(errors="replace")
                except Exception:
                    continue
                # Match: struct ContentView: View
                if re.search(rf"struct\s+{re.escape(root_view)}\s*:", source):
                    # Detect "else { LoginView() }" or "!isAuthenticated ... LoginView()"
                    if re.search(r"else\s*\{[^}]*Login\w*\s*\(", source, re.DOTALL):
                        self._login_is_entry = True
                        return "LoginView"
                    if re.search(r"!.*(?:isAuthenticated|isLoggedIn).*Login\w*\s*\(", source, re.DOTALL):
                        self._login_is_entry = True
                        return "LoginView"
                    # No login guard — root view is the entry
                    return root_view

        # Fallback: first screen
        if self._screens:
            return self._screens[0].name
        return None

    def _build_reachability(self) -> Dict[str, List[str]]:
        """BFS from entry point to build shortest paths to each screen."""
        if not self._entry_point:
            return {}

        # Build adjacency
        adj: Dict[str, Set[str]] = {}
        for a in self._actions:
            if a.destination:
                adj.setdefault(a.source, set()).add(a.destination)

        # BFS
        visited: Dict[str, List[str]] = {self._entry_point: [self._entry_point]}
        queue = [self._entry_point]

        while queue:
            current = queue.pop(0)
            for neighbor in adj.get(current, []):
                if neighbor not in visited:
                    visited[neighbor] = visited[current] + [neighbor]
                    queue.append(neighbor)

        return visited
