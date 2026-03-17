"""Appium-based live accessibility discovery for iOS Simulator apps."""
import asyncio
import logging
import subprocess
import time
from typing import List, Optional

import httpx

from app.utils.accessibility_tree_parser import AccessibilitySnapshot, parse_wda_xml

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
                ["appium", "--port", "4723", "--log-level", "error",
                 "--allow-insecure", "chromedriver_autodownload"],
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

    def _kill_wda(self, device_udid: str):
        """
        Robustly kill all WebDriverAgent processes to free testmanagerd.
        
        WDA blocks testmanagerd connection needed by xcodebuild test runner.
        Must verify processes are dead before proceeding.
        """
        logger.info("Killing WebDriverAgent processes...")
        
        # Step 1: Graceful termination via simctl
        try:
            subprocess.run(
                ["xcrun", "simctl", "terminate", device_udid, "com.apple.test.WebDriverAgentRunner-Runner"],
                capture_output=True,
                timeout=3
            )
        except Exception as e:
            logger.warning(f"simctl terminate failed: {e}")
        
        # Step 2: SIGTERM all WDA PIDs
        try:
            result = subprocess.run(
                ["pgrep", "-f", "WebDriverAgent"],
                capture_output=True,
                text=True,
                timeout=2
            )
            pids = result.stdout.strip().split('\n') if result.returncode == 0 else []
            pids = [p for p in pids if p]  # Filter empty
            
            if pids:
                logger.info(f"Found WDA PIDs: {pids}")
                for pid in pids:
                    try:
                        subprocess.run(["kill", "-TERM", pid], timeout=1)
                    except Exception:
                        pass
        except Exception as e:
            logger.warning(f"pgrep/kill failed: {e}")
        
        # Step 3: Poll for up to 5s to confirm death
        deadline = time.time() + 5
        escalated = False
        
        while time.time() < deadline:
            try:
                result = subprocess.run(
                    ["pgrep", "-f", "WebDriverAgent"],
                    capture_output=True,
                    timeout=1
                )
                if result.returncode != 0:  # No processes found
                    logger.info("All WDA processes confirmed dead")
                    time.sleep(1)  # Settle time for testmanagerd to release
                    return
            except Exception:
                pass
            
            # Escalate to SIGKILL after 3s
            if not escalated and time.time() - deadline + 5 > 3:
                logger.warning("WDA still alive after 3s, escalating to SIGKILL")
                try:
                    subprocess.run(
                        ["pkill", "-9", "-f", "WebDriverAgent"],
                        timeout=2
                    )
                except Exception:
                    pass
                escalated = True
            
            time.sleep(0.5)
        
        logger.warning("WDA kill timeout reached, some processes may still be alive")

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    async def discover(
        self,
        bundle_id: str,
        device_udid: str,
        screen_hints: Optional[List[str]] = None,
        discovery_timeout: int = 60,
    ) -> AccessibilitySnapshot:
        """
        Launch app via Appium, capture accessibility tree + screenshot.

        Args:
            bundle_id: App bundle ID e.g. "com.example.MyApp"
            device_udid: UDID of already-booted iOS Simulator
            screen_hints: Optional list of screen names to try navigating to
            discovery_timeout: Max seconds to wait for elements

        Returns:
            AccessibilitySnapshot with elements and screenshot
        """
        if not self.is_server_running():
            logger.warning("Appium server not running, attempting auto-start...")
            if not self.start_appium_server():
                logger.error("Cannot connect to Appium server")
                return AccessibilitySnapshot(bundle_id=bundle_id, device_udid=device_udid)

        loop = asyncio.get_event_loop()
        snapshot = await loop.run_in_executor(
            None,
            self._discover_sync,
            bundle_id, device_udid, screen_hints, discovery_timeout
        )
        return snapshot

    def _discover_sync(
        self,
        bundle_id: str,
        device_udid: str,
        screen_hints: Optional[List[str]],
        discovery_timeout: int,
    ) -> AccessibilitySnapshot:
        """Synchronous discovery — runs in thread executor."""
        try:
            from appium import webdriver
            from appium.options import XCUITestOptions
        except ImportError:
            logger.error(
                "Appium-Python-Client not installed. Run: pip install Appium-Python-Client"
            )
            return AccessibilitySnapshot(bundle_id=bundle_id, device_udid=device_udid)

        opts = XCUITestOptions()
        opts.platform_name = "iOS"
        opts.bundle_id = bundle_id
        opts.udid = device_udid
        opts.no_reset = True
        opts.automation_name = "XCUITest"
        opts.new_command_timeout = discovery_timeout
        opts.should_use_singleton_test_manager = False

        driver = None
        try:
            logger.info("Connecting to Appium for bundle_id=%s udid=%s", bundle_id, device_udid)
            driver = webdriver.Remote(self.server_url, options=opts)

            # Brief wait for app to settle
            time.sleep(2)

            # Capture page source (live accessibility tree XML)
            logger.info("Capturing accessibility tree...")
            xml = driver.page_source

            # Capture screenshot
            logger.info("Capturing screenshot...")
            screenshot_b64 = driver.get_screenshot_as_base64()

            elements = parse_wda_xml(xml)
            logger.info(
                "Discovered %d total elements, %d interactive with IDs",
                len(elements),
                len([e for e in elements if e.is_interactive and e.has_useful_name]),
            )

            return AccessibilitySnapshot(
                elements=elements,
                screenshot_b64=screenshot_b64,
                raw_xml=xml,
                bundle_id=bundle_id,
                device_udid=device_udid,
            )

        except Exception as e:
            logger.error("Appium discovery failed: %s", e, exc_info=True)
            return AccessibilitySnapshot(bundle_id=bundle_id, device_udid=device_udid)
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass
            
            # Critical: Kill all WDA processes to free testmanagerd for xcodebuild
            self._kill_wda(device_udid)
