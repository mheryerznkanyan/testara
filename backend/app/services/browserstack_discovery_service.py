"""BrowserStack-based cloud discovery — captures accessibility tree from real devices."""
import asyncio
import logging
import time
from typing import Optional

from app.utils.accessibility_tree_parser import MultiScreenSnapshot

logger = logging.getLogger(__name__)

BS_HUB_URL = "https://hub-cloud.browserstack.com/wd/hub"


class BrowserStackDiscoveryService:
    """Discovers app accessibility tree via BrowserStack App Automate.

    Connects to a real iOS device on BrowserStack, launches the app,
    and runs the same multi-screen discovery logic as local Appium.
    No local Appium server, Xcode, or simulator required.
    """

    def __init__(self, username: str, access_key: str):
        self.username = username
        self.access_key = access_key

    async def discover(
        self,
        app_url: str,
        device_name: str = "iPhone 15 Pro",
        os_version: str = "17",
        discovery_timeout: int = 120,
    ) -> MultiScreenSnapshot:
        """Launch app on BrowserStack and capture accessibility tree.

        Args:
            app_url: BrowserStack app URL (bs://...) from prior upload
            device_name: Device to run on (e.g. "iPhone 15 Pro")
            os_version: iOS version (e.g. "17")
            discovery_timeout: Max seconds for the entire discovery session
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._discover_sync,
            app_url, device_name, os_version, discovery_timeout,
        )

    def _discover_sync(
        self,
        app_url: str,
        device_name: str,
        os_version: str,
        discovery_timeout: int,
    ) -> MultiScreenSnapshot:
        try:
            from appium import webdriver
            from appium.options.ios import XCUITestOptions
        except ImportError:
            logger.error("Appium-Python-Client not installed")
            return MultiScreenSnapshot()

        from app.services.discovery_helpers import discover_screens

        opts = XCUITestOptions()
        opts.platform_name = "iOS"
        opts.automation_name = "XCUITest"
        opts.new_command_timeout = discovery_timeout
        opts.no_reset = True
        opts.set_capability("appium:app", app_url)
        opts.set_capability("bstack:options", {
            "userName": self.username,
            "accessKey": self.access_key,
            "deviceName": device_name,
            "osVersion": os_version,
            "projectName": "Testara",
            "buildName": "Cloud Discovery",
            "sessionName": "app-discovery",
            "networkLogs": False,
            "deviceLogs": True,
        })

        driver = None
        try:
            logger.info(
                "Cloud discovery: connecting to %s on %s iOS %s...",
                app_url, device_name, os_version,
            )
            driver = webdriver.Remote(BS_HUB_URL, options=opts)
            logger.info("Cloud discovery: session started (id=%s)", driver.session_id)

            # BrowserStack launches the app fresh — wait for it to load
            time.sleep(4)

            # Run the same multi-screen discovery as local
            screens = discover_screens(driver)

            # Mark session as passed on BrowserStack
            import json
            try:
                driver.execute_script("browserstack_executor: " + json.dumps({
                    "action": "setSessionStatus",
                    "arguments": {
                        "status": "passed",
                        "reason": f"Discovery complete: {len(screens)} screens",
                    },
                }))
            except Exception:
                pass

            return MultiScreenSnapshot(
                screens=screens,
                bundle_id="",
                device_udid=f"bs:{device_name}:{os_version}",
            )

        except Exception as e:
            logger.error("Cloud discovery failed: %s", e, exc_info=True)
            # Mark session as failed
            if driver:
                import json
                try:
                    driver.execute_script("browserstack_executor: " + json.dumps({
                        "action": "setSessionStatus",
                        "arguments": {"status": "failed", "reason": str(e)[:200]},
                    }))
                except Exception:
                    pass
            return MultiScreenSnapshot()

        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass
