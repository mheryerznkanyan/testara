"""LLM-guided Appium navigation for multi-screen accessibility discovery."""
import logging
import time
from typing import List, Optional

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.prompts import NAVIGATION_ELEMENT_PROMPT
from app.utils.accessibility_tree_parser import (
    AccessibilitySnapshot,
    ElementInfo,
    MultiScreenSnapshot,
    ScreenCapture,
    parse_wda_xml,
)

logger = logging.getLogger(__name__)

# Element types most likely to trigger navigation
_NAV_ELEMENT_TYPES = {
    "XCUIElementTypeButton",
    "XCUIElementTypeCell",
    "XCUIElementTypeLink",
    "XCUIElementTypeStaticText",
    "XCUIElementTypeTab",
}


def _screen_base_name(screen_name: str) -> str:
    """Extract base name: 'SettingsView' -> 'settings', 'LoginViewController' -> 'login'."""
    name = screen_name
    for suffix in ("ViewController", "Controller", "View", "Screen"):
        if name.endswith(suffix) and len(name) > len(suffix):
            name = name[: -len(suffix)]
            break
    return name.lower()


class AppiumNavigator:
    """Navigate an iOS app through screens using Appium, capturing accessibility trees."""

    def __init__(self, driver, llm=None, max_steps: int = 5, settle_time: float = 2.5):
        self._driver = driver
        self._llm = llm
        self._max_steps = max_steps
        self._settle_time = settle_time

    def navigate_and_capture(
        self, nav_path: List[str], bundle_id: str = "", device_udid: str = ""
    ) -> MultiScreenSnapshot:
        """Navigate along nav_path, capturing snapshots at each screen.

        Args:
            nav_path: Ordered list of screen names from entry to target.
                      e.g. ["ContentView", "HomeView", "SettingsView"]
            bundle_id: App bundle ID for metadata.
            device_udid: Device UDID for metadata.

        Returns:
            MultiScreenSnapshot with captures from each visited screen.
        """
        result = MultiScreenSnapshot(
            navigation_path=nav_path,
            bundle_id=bundle_id,
            device_udid=device_udid,
        )

        if not nav_path:
            # No path — just capture current screen
            snapshot = self._capture_current_screen()
            result.screens.append(
                ScreenCapture(screen_name="initial", snapshot=snapshot, is_target=True)
            )
            return result

        # Capture the initial screen (first in path)
        snapshot = self._capture_current_screen()

        is_target = len(nav_path) == 1
        result.screens.append(
            ScreenCapture(screen_name=nav_path[0], snapshot=snapshot, is_target=is_target)
        )

        if is_target:
            return result

        # Navigate through intermediate screens to reach target
        for step_idx in range(1, len(nav_path)):
            if step_idx > self._max_steps:
                logger.warning("Max navigation steps (%d) reached, stopping", self._max_steps)
                break

            target_screen = nav_path[step_idx]
            is_last = step_idx == len(nav_path) - 1

            logger.info(
                "Navigation step %d/%d: looking for element leading to %s",
                step_idx, len(nav_path) - 1, target_screen,
            )

            # Try to find and tap the right element
            interactive = snapshot.interactive_elements()
            element_id = self._find_navigation_element(interactive, target_screen)

            if not element_id:
                logger.warning(
                    "Could not find element for screen %s, stopping navigation", target_screen
                )
                break

            # Tap the element
            if not self._find_and_tap(element_id):
                logger.warning("Failed to tap element %r, stopping navigation", element_id)
                break

            # Wait for screen transition
            time.sleep(self._settle_time)

            # Capture the new screen after navigation
            snapshot = self._capture_current_screen()

            result.screens.append(
                ScreenCapture(
                    screen_name=target_screen,
                    snapshot=snapshot,
                    is_target=is_last,
                )
            )

            logger.info("Navigated to %s (%d interactive elements)", target_screen,
                        len(snapshot.interactive_elements()))

        # If we didn't reach the target, mark the last screen as target
        if not any(sc.is_target for sc in result.screens):
            result.screens[-1].is_target = True

        return result

    def _capture_current_screen(self) -> AccessibilitySnapshot:
        """Capture accessibility tree and screenshot from current screen."""
        xml = self._driver.page_source
        screenshot_b64 = ""
        try:
            screenshot_b64 = self._driver.get_screenshot_as_base64()
        except Exception:
            pass
        elements = parse_wda_xml(xml)
        return AccessibilitySnapshot(elements=elements, screenshot_b64=screenshot_b64, raw_xml=xml)

    def _find_navigation_element(
        self, interactive: List[ElementInfo], target_screen: str
    ) -> Optional[str]:
        """Find which element to tap to navigate to target_screen.

        Strategy:
        1. Direct string matching (fast, no LLM)
        2. LLM fallback (only if direct match fails)
        """
        base = _screen_base_name(target_screen)

        # Strategy 1: Direct match — look for elements whose name/label contains the screen base name
        candidates = []
        for e in interactive:
            name_lower = e.name.lower()
            label_lower = e.label.lower()

            # Exact match on base name
            if base == name_lower or base == label_lower:
                identifier = e.name if e.has_useful_name else e.label
                logger.info("Direct exact match: %r for screen %s", identifier, target_screen)
                return identifier

            # Contains match — prefer nav-type elements
            if base in name_lower or base in label_lower:
                priority = 0 if e.element_type in _NAV_ELEMENT_TYPES else 1
                identifier = e.name if e.has_useful_name else e.label
                candidates.append((priority, identifier))

        if candidates:
            candidates.sort(key=lambda x: x[0])
            identifier = candidates[0][1]
            logger.info("Direct contains match: %r for screen %s", identifier, target_screen)
            return identifier

        # Strategy 2: LLM fallback
        if self._llm:
            return self._ask_llm_for_element(interactive, target_screen)

        logger.warning("No match found for screen %s and no LLM available", target_screen)
        return None

    def _ask_llm_for_element(
        self, interactive: List[ElementInfo], target_screen: str
    ) -> Optional[str]:
        """Ask LLM which element to tap (fallback when direct matching fails)."""
        elements_text = "\n".join(
            f"- [{e.short_type}] name={e.name!r} label={e.label!r}"
            for e in interactive
        )
        user_msg = (
            f"Current screen interactive elements:\n{elements_text}\n\n"
            f"Target screen: {target_screen}\n"
            f"Which element should I tap?"
        )

        try:
            logger.info("Asking LLM for navigation element to reach %s", target_screen)
            response = self._llm.invoke([
                SystemMessage(content=NAVIGATION_ELEMENT_PROMPT),
                HumanMessage(content=user_msg),
            ])
            answer = response.content.strip().strip('"').strip("'")

            if answer.upper() == "NONE":
                logger.info("LLM says no element leads to %s", target_screen)
                return None

            logger.info("LLM suggests element: %r for screen %s", answer, target_screen)
            return answer
        except Exception as e:
            logger.warning("LLM navigation query failed: %s", e)
            return None

    def _find_and_tap(self, identifier: str) -> bool:
        """Find element by identifier and tap it."""
        try:
            from appium.webdriver.common.appiumby import AppiumBy
        except ImportError:
            logger.error("AppiumBy not available")
            return False

        # Try accessibility ID first
        strategies = [
            (AppiumBy.ACCESSIBILITY_ID, identifier),
            (AppiumBy.NAME, identifier),
            (AppiumBy.XPATH, f'//*[@label="{identifier}"]'),
        ]

        for by, value in strategies:
            try:
                element = self._driver.find_element(by, value)
                element.click()
                logger.info("Tapped element via %s=%r", by, value)
                return True
            except Exception:
                continue

        logger.warning("Could not find element with identifier %r", identifier)
        return False
