"""Appium-based live accessibility discovery for iOS Simulator apps."""
import asyncio
import logging
import subprocess
import time
from typing import List, Optional

import httpx

from app.utils.accessibility_tree_parser import (
    AccessibilitySnapshot,
    MultiScreenSnapshot,
    ScreenCapture,
    parse_wda_xml,
)

logger = logging.getLogger(__name__)

INTERACTIVE_XPATH_TYPES = [
    "XCUIElementTypeButton",
    "XCUIElementTypeTextField",
    "XCUIElementTypeSecureTextField",
    "XCUIElementTypeSwitch",
    "XCUIElementTypeSearchField",
    "XCUIElementTypeCell",
]


class AppiumDiscoveryService:
    """Discovers runtime accessibility tree from a running iOS app via Appium/WDA."""

    def __init__(self, server_url: str = "http://localhost:4723", startup_timeout: int = 30):
        self.server_url = server_url
        self.startup_timeout = startup_timeout
        self._server_proc: Optional[subprocess.Popen] = None

    # ------------------------------------------------------------------
    # Server lifecycle
    # ------------------------------------------------------------------

    def is_server_running(self) -> bool:
        """Check if Appium server is responding."""
        try:
            resp = httpx.get(f"{self.server_url}/status", timeout=3.0)
            return resp.status_code == 200
        except Exception:
            return False

    def start_appium_server(self) -> bool:
        """Start Appium server as a subprocess if not already running."""
        if self.is_server_running():
            logger.info("Appium server already running at %s", self.server_url)
            return True

        logger.info("Starting Appium server...")
        try:
            self._server_proc = subprocess.Popen(
                ["appium", "--port", "4723", "--log-level", "error"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError:
            logger.error(
                "Appium not found. Install: npm install -g appium && appium driver install xcuitest"
            )
            return False

        # Wait for server to be ready
        deadline = time.time() + self.startup_timeout
        while time.time() < deadline:
            if self.is_server_running():
                logger.info("Appium server started successfully")
                return True
            time.sleep(1)

        logger.error("Appium server did not start within %ds", self.startup_timeout)
        return False

    def stop(self):
        """Stop the managed Appium server process."""
        if self._server_proc and self._server_proc.poll() is None:
            logger.info("Stopping Appium server...")
            self._server_proc.terminate()
            try:
                self._server_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._server_proc.kill()
            self._server_proc = None

    @staticmethod
    def _kill_wda(device_udid: str):
        """Kill any WebDriverAgent processes and wait for testmanagerd to be released.

        WDA holds the testmanagerd connection, which prevents xcodebuild's
        test runner from connecting.  Must be killed after discovery so that
        subsequent test execution works.
        """
        try:
            # Step 1: Graceful termination via simctl
            subprocess.run(
                ["xcrun", "simctl", "terminate", device_udid,
                 "com.facebook.WebDriverAgentRunner.xctrunner"],
                capture_output=True,
            )

            # Step 2: Find and SIGTERM all WDA processes
            def _find_wda_pids() -> list:
                pids = set()
                for pattern in ["WebDriverAgentRunner", "WebDriverAgent"]:
                    result = subprocess.run(
                        ["pgrep", "-f", pattern],
                        capture_output=True, text=True,
                    )
                    if result.stdout.strip():
                        pids.update(result.stdout.strip().split("\n"))
                return [p.strip() for p in pids if p.strip()]

            pids = _find_wda_pids()
            if pids:
                for pid in pids:
                    try:
                        subprocess.run(["kill", pid], capture_output=True)
                    except Exception:
                        pass
                logger.info("Sent SIGTERM to %d WDA process(es)", len(pids))

            # Step 3: Poll until processes die (up to 5s), escalate to SIGKILL after 3s
            deadline = time.time() + 5
            escalated = False
            while time.time() < deadline:
                remaining = _find_wda_pids()
                if not remaining:
                    logger.info("All WDA processes confirmed dead")
                    break
                if not escalated and time.time() > deadline - 2:
                    # 3s elapsed, escalate to SIGKILL
                    for pid in remaining:
                        try:
                            subprocess.run(["kill", "-9", pid], capture_output=True)
                        except Exception:
                            pass
                    logger.warning("Escalated to SIGKILL for %d lingering WDA process(es)", len(remaining))
                    escalated = True
                time.sleep(0.5)
            else:
                remaining = _find_wda_pids()
                if remaining:
                    logger.error("WDA processes still alive after 5s: PIDs %s", remaining)

            # Step 4: Settle time for testmanagerd to release the connection
            time.sleep(1)

        except Exception as e:
            logger.warning("Failed to kill WDA processes: %s", e)

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    async def discover(
        self,
        bundle_id: str,
        device_udid: str,
        navigation_path: Optional[List[str]] = None,
        llm=None,
        discovery_timeout: int = 60,
    ) -> MultiScreenSnapshot:
        """
        Launch app via Appium, optionally navigate to target screen,
        and capture accessibility trees along the way.

        Args:
            bundle_id: App bundle ID e.g. "com.example.MyApp"
            device_udid: UDID of already-booted iOS Simulator
            navigation_path: Ordered screen names to navigate through
            llm: LLM instance for fallback element matching during navigation
            discovery_timeout: Max seconds to wait for elements

        Returns:
            MultiScreenSnapshot with captures from all visited screens
        """
        if not self.is_server_running():
            logger.warning("Appium server not running, attempting auto-start...")
            if not self.start_appium_server():
                logger.error("Cannot connect to Appium server")
                return MultiScreenSnapshot(bundle_id=bundle_id, device_udid=device_udid)

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            self._discover_sync,
            bundle_id, device_udid, navigation_path, llm, discovery_timeout,
        )
        return result

    def _discover_sync(
        self,
        bundle_id: str,
        device_udid: str,
        navigation_path: Optional[List[str]],
        llm,
        discovery_timeout: int,
    ) -> MultiScreenSnapshot:
        """Synchronous discovery — runs in thread executor."""
        try:
            from appium import webdriver
            from appium.options.common.base import AppiumOptions
        except ImportError:
            logger.error(
                "Appium-Python-Client not installed. Run: pip install Appium-Python-Client"
            )
            return MultiScreenSnapshot(bundle_id=bundle_id, device_udid=device_udid)

        opts = AppiumOptions()
        opts.set_capability("platformName", "iOS")
        opts.set_capability("appium:bundleId", bundle_id)
        opts.set_capability("appium:udid", device_udid)
        opts.set_capability("appium:noReset", True)
        opts.set_capability("appium:automationName", "XCUITest")
        opts.set_capability("appium:newCommandTimeout", discovery_timeout)
        opts.set_capability("appium:shouldUseSingletonTestManager", False)

        driver = None
        try:
            logger.info("Connecting to Appium for bundle_id=%s udid=%s", bundle_id, device_udid)
            driver = webdriver.Remote(self.server_url, options=opts)

            # Brief wait for app to settle
            time.sleep(2)

            if navigation_path and len(navigation_path) > 1:
                # Multi-screen navigation
                from app.services.appium_navigator import AppiumNavigator

                navigator = AppiumNavigator(driver=driver, llm=llm)
                result = navigator.navigate_and_capture(
                    nav_path=navigation_path,
                    bundle_id=bundle_id,
                    device_udid=device_udid,
                )
                logger.info(
                    "Multi-screen discovery complete: %d screens captured, path: %s",
                    len(result.screens),
                    " -> ".join(sc.screen_name for sc in result.screens),
                )
                return result
            else:
                # Single-screen capture (original behavior)
                logger.info("Capturing accessibility tree...")
                xml = driver.page_source
                screenshot_b64 = driver.get_screenshot_as_base64()
                elements = parse_wda_xml(xml)

                logger.info(
                    "Discovered %d total elements, %d interactive with IDs",
                    len(elements),
                    len([e for e in elements if e.is_interactive and e.has_useful_name]),
                )

                snapshot = AccessibilitySnapshot(
                    elements=elements,
                    screenshot_b64=screenshot_b64,
                    raw_xml=xml,
                    bundle_id=bundle_id,
                    device_udid=device_udid,
                )

                screen_name = navigation_path[0] if navigation_path else "initial"
                return MultiScreenSnapshot(
                    screens=[ScreenCapture(screen_name=screen_name, snapshot=snapshot, is_target=True)],
                    navigation_path=navigation_path or [],
                    bundle_id=bundle_id,
                    device_udid=device_udid,
                )

        except Exception as e:
            logger.error("Appium discovery failed: %s", e, exc_info=True)
            return MultiScreenSnapshot(bundle_id=bundle_id, device_udid=device_udid)
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass
            # Kill WDA processes left behind by Appium — they block xcodebuild's
            # test runner from connecting to the simulator's testmanagerd.
            self._kill_wda(device_udid)
