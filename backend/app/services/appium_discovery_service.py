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
    ) -> MultiScreenSnapshot:
        """
        Launch app via Appium, capture accessibility trees from multiple screens.

        Resets the app, captures the home screen, then navigates through tabs
        and tappable filter/section buttons to capture sub-screens.

        Returns:
            MultiScreenSnapshot with elements from all discovered screens
        """
        if not self.is_server_running():
            logger.warning("Appium server not running, attempting auto-start...")
            if not self.start_appium_server():
                logger.error("Cannot connect to Appium server")
                return MultiScreenSnapshot(bundle_id=bundle_id, device_udid=device_udid)

        loop = asyncio.get_event_loop()
        snapshot = await loop.run_in_executor(
            None,
            self._discover_sync,
            bundle_id, device_udid, screen_hints, discovery_timeout
        )
        return snapshot

    def _try_auto_login(self, driver) -> None:
        """Attempt auto-login if a login screen is detected and credentials are configured."""
        from app.core.config import settings
        from appium.webdriver.common.appiumby import AppiumBy

        email = settings.test_credentials_email
        password = settings.test_credentials_password
        if not email or not password:
            return

        # Common login field IDs (app-specific first, then generic)
        email_ids = ["emailTextField", "email_field", "usernameField", "email", "Email"]
        password_ids = ["passwordTextField", "password_field", "passwordField", "password", "Password"]
        login_btn_ids = ["loginButton", "login_button", "signInButton", "Log in", "Sign in"]

        email_field = None
        for fid in email_ids:
            try:
                el = driver.find_element(AppiumBy.ACCESSIBILITY_ID, fid)
                if el.is_displayed():
                    email_field = el
                    break
            except Exception:
                continue

        if not email_field:
            logger.debug("No login screen detected, skipping auto-login")
            return

        logger.info("Login screen detected, entering credentials...")
        email_field.clear()
        email_field.send_keys(email)

        for pid in password_ids:
            try:
                pwd_field = driver.find_element(AppiumBy.ACCESSIBILITY_ID, pid)
                if pwd_field.is_displayed():
                    pwd_field.clear()
                    pwd_field.send_keys(password)
                    break
            except Exception:
                continue

        for bid in login_btn_ids:
            try:
                btn = driver.find_element(AppiumBy.ACCESSIBILITY_ID, bid)
                if btn.is_displayed():
                    btn.click()
                    time.sleep(3)
                    logger.info("Auto-login completed")
                    return
            except Exception:
                continue

        logger.warning("Could not find login button after entering credentials")

    def _capture_screen(self, driver, label: str, nav_path: str = "", wait_for_stable: bool = True) -> ScreenCapture:
        """Capture current screen's accessibility tree.

        If wait_for_stable=True, polls page_source until element count
        stabilizes (no new elements for 2 consecutive checks, up to 10s).
        This handles async-loading content like filter options and lists.
        """
        if wait_for_stable:
            prev_count = 0
            stable_checks = 0
            deadline = time.time() + 10

            while time.time() < deadline:
                xml = driver.page_source
                elements = parse_wda_xml(xml)
                interactive = [e for e in elements if e.is_interactive and e.has_useful_name]
                current_count = len(interactive)

                if current_count == prev_count and current_count > 0:
                    stable_checks += 1
                    if stable_checks >= 2:
                        break
                else:
                    stable_checks = 0
                    prev_count = current_count

                time.sleep(1)
        else:
            xml = driver.page_source
            elements = parse_wda_xml(xml)
            interactive = [e for e in elements if e.is_interactive and e.has_useful_name]

        # Scroll to reveal off-screen elements — skip on large screens (project lists)
        interactive = [e for e in elements if e.is_interactive and e.has_useful_name]
        should_scroll = len(interactive) < 200
        if not should_scroll:
            logger.info("  Screen '%s': skipping scroll (%d elements already)", label, len(interactive))
        if should_scroll:
            try:
                from appium.webdriver.common.appiumby import AppiumBy
                scrollable = driver.find_elements(AppiumBy.IOS_CLASS_CHAIN,
                    "**/XCUIElementTypeScrollView")
                if scrollable:
                    size = driver.get_window_size()
                    start_y = int(size['height'] * 0.8)
                    end_y = int(size['height'] * 0.3)
                    mid_x = int(size['width'] * 0.5)
                    driver.swipe(mid_x, start_y, mid_x, end_y, duration=500)
                    time.sleep(1)

                    xml2 = driver.page_source
                    extra_elements = parse_wda_xml(xml2)
                    existing_names = {(e.element_type, e.name) for e in elements if e.name}
                    for e in extra_elements:
                        if e.name and (e.element_type, e.name) not in existing_names:
                            elements.append(e)
                            existing_names.add((e.element_type, e.name))

                    driver.swipe(mid_x, end_y, mid_x, start_y, duration=500)
                    time.sleep(0.5)
            except Exception:
                pass

        interactive = [e for e in elements if e.is_interactive and e.has_useful_name]
        screenshot_b64 = driver.get_screenshot_as_base64()

        logger.info(
            "  Screen '%s': %d elements, %d interactive",
            label, len(elements), len(interactive),
        )
        return ScreenCapture(
            screen_label=label,
            elements=elements,
            screenshot_b64=screenshot_b64,
            navigation_path=nav_path,
        )

    def _discover_sync(
        self,
        bundle_id: str,
        device_udid: str,
        screen_hints: Optional[List[str]],
        discovery_timeout: int,
    ) -> MultiScreenSnapshot:
        """Multi-screen discovery — captures home screen, tabs, and sub-screens."""
        try:
            from appium import webdriver
            from appium.options.ios import XCUITestOptions
            from appium.webdriver.common.appiumby import AppiumBy
        except ImportError:
            logger.error(
                "Appium-Python-Client not installed. Run: pip install Appium-Python-Client"
            )
            return MultiScreenSnapshot(bundle_id=bundle_id, device_udid=device_udid)

        opts = XCUITestOptions()
        opts.platform_name = "iOS"
        opts.bundle_id = bundle_id
        opts.udid = device_udid
        opts.no_reset = True
        opts.automation_name = "XCUITest"
        opts.new_command_timeout = discovery_timeout
        opts.should_use_singleton_test_manager = False

        driver = None
        screens: List[ScreenCapture] = []

        try:
            logger.info("Multi-screen discovery for bundle_id=%s", bundle_id)
            driver = webdriver.Remote(self.server_url, options=opts)

            # Reset app to home screen
            driver.terminate_app(bundle_id)
            time.sleep(1)
            driver.activate_app(bundle_id)
            time.sleep(2)

            # Auto-login if credentials are configured and a login screen is detected
            self._try_auto_login(driver)

            # 1. Capture home screen (post-login if applicable)
            screens.append(self._capture_screen(driver, "Home"))

            # 2. Discover tab bar buttons and navigate to each tab
            home_elements = screens[0].elements
            tab_names = []
            for e in home_elements:
                if e.element_type == "XCUIElementTypeButton" and e.has_useful_name:
                    # Tab bar buttons are typically at the bottom of the screen (y > 750)
                    if e.y > 700 and e.name not in tab_names:
                        tab_names.append(e.name)

            logger.info("Detected tab bar buttons: %s", tab_names)

            for tab_name in tab_names:
                try:
                    tab_el = driver.find_element(AppiumBy.ACCESSIBILITY_ID, tab_name)
                    tab_el.click()
                    time.sleep(1.5)

                    screen = self._capture_screen(
                        driver,
                        label=tab_name,
                        nav_path=f"tap '{tab_name}' tab",
                    )
                    screens.append(screen)

                    # 3. On each tab screen, try tapping expandable sections
                    #    (buttons that reveal sub-content like filters)
                    tappable = [
                        e for e in screen.interactive_elements()
                        if e.element_type == "XCUIElementTypeButton"
                        and e.has_useful_name
                        and e.y < 700  # not tab bar
                        and e.name not in tab_names  # not another tab
                        and e.name not in ("Cancel", "Close", "Back", "Done",
                                           "See results", "Reset all", "icon  cross")
                    ]

                    for btn in tappable[:5]:  # cap at 5 sub-screens per tab
                        try:
                            # Remember current element names before clicking
                            pre_click_names = {
                                e.name for e in parse_wda_xml(driver.page_source)
                                if e.is_interactive and e.has_useful_name
                            }

                            btn_el = driver.find_element(AppiumBy.ACCESSIBILITY_ID, btn.name)
                            btn_el.click()

                            # Wait up to 8s for new elements to appear
                            deadline = time.time() + 8
                            sub_screen = None
                            while time.time() < deadline:
                                time.sleep(1)
                                candidate = self._capture_screen(
                                    driver,
                                    label=f"{tab_name} > {btn.name}",
                                    nav_path=f"tap '{tab_name}' tab, then tap '{btn.name}'",
                                )
                                current_names = {
                                    e.name for e in candidate.interactive_elements()
                                }
                                new_names = current_names - pre_click_names
                                if new_names:
                                    sub_screen = candidate
                                    break

                            if sub_screen:
                                new_count = len({
                                    e.name for e in sub_screen.interactive_elements()
                                } - {e.name for e in screen.interactive_elements()})
                                screens.append(sub_screen)
                                logger.info(
                                    "  Sub-screen '%s > %s' revealed %d new elements",
                                    tab_name, btn.name, new_count,
                                )
                            else:
                                logger.debug(
                                    "  Sub-screen '%s > %s' — no new elements after 8s",
                                    tab_name, btn.name,
                                )

                            # Navigate back (tap back button or same button to collapse)
                            try:
                                back = driver.find_element(AppiumBy.ACCESSIBILITY_ID, "BackButton")
                                back.click()
                            except Exception:
                                try:
                                    btn_el = driver.find_element(AppiumBy.ACCESSIBILITY_ID, btn.name)
                                    btn_el.click()
                                except Exception:
                                    pass
                            time.sleep(1)

                        except Exception as e:
                            logger.debug("Could not explore sub-screen '%s': %s", btn.name, e)

                except Exception as e:
                    logger.debug("Could not navigate to tab '%s': %s", tab_name, e)

            total_interactive = len(MultiScreenSnapshot(screens=screens).all_interactive_elements())
            logger.info(
                "Multi-screen discovery complete: %d screens, %d unique interactive elements",
                len(screens), total_interactive,
            )

            return MultiScreenSnapshot(
                screens=screens,
                bundle_id=bundle_id,
                device_udid=device_udid,
            )

        except Exception as e:
            logger.error("Multi-screen discovery failed: %s", e, exc_info=True)
            return MultiScreenSnapshot(bundle_id=bundle_id, device_udid=device_udid)
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass
            self._kill_wda(device_udid)
