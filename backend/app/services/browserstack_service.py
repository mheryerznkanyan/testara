"""BrowserStack App Automate integration for Testara cloud execution."""
import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, Optional

import aiohttp

logger = logging.getLogger(__name__)

BS_HUB_URL = "https://hub-cloud.browserstack.com/wd/hub"
BS_UPLOAD_URL = "https://api-cloud.browserstack.com/app-automate/upload"
BS_DEVICES_URL = "https://api-cloud.browserstack.com/app-automate/devices.json"


# Default iOS device presets for common test scenarios
DEFAULT_DEVICES = [
    {"device": "iPhone 15 Pro", "os_version": "17"},
    {"device": "iPhone 14",     "os_version": "16"},
    {"device": "iPhone 13",     "os_version": "15"},
    {"device": "iPad Pro 12.9 2022", "os_version": "16"},
]


class BrowserStackService:
    """
    Handles BrowserStack App Automate interactions:
      - App upload (.ipa → bs:// URL)
      - Available device listing
      - Capability generation for the Appium harness
    """

    def __init__(self, username: str, access_key: str):
        if not username or not access_key:
            raise ValueError("BrowserStack username and access_key are required")
        self.username = username
        self.access_key = access_key
        self._auth = aiohttp.BasicAuth(username, access_key)
        # Cache uploaded app URLs: ipa_path → bs:// url
        self._app_url_cache: Dict[str, str] = {}

    # ------------------------------------------------------------------
    # App upload
    # ------------------------------------------------------------------

    async def upload_app(self, ipa_path: str, custom_id: Optional[str] = None) -> str:
        """
        Upload an .ipa to BrowserStack and return the bs:// app URL.
        Results are cached by file path to avoid redundant uploads.
        """
        ipa_path = str(ipa_path)
        if ipa_path in self._app_url_cache:
            logger.info("Using cached BS app URL for %s", ipa_path)
            return self._app_url_cache[ipa_path]

        path = Path(ipa_path)
        if not path.exists():
            raise FileNotFoundError(f"IPA not found: {ipa_path}")

        logger.info("Uploading app to BrowserStack: %s", path.name)

        data = aiohttp.FormData()
        data.add_field("file", open(ipa_path, "rb"), filename=path.name)
        if custom_id:
            data.add_field("custom_id", custom_id)

        async with aiohttp.ClientSession() as session:
            async with session.post(
                BS_UPLOAD_URL,
                data=data,
                auth=self._auth,
                timeout=aiohttp.ClientTimeout(total=120),
            ) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    raise RuntimeError(f"BS upload failed ({resp.status}): {body}")
                result = await resp.json()

        app_url = result.get("app_url")
        if not app_url:
            raise RuntimeError(f"BS upload returned no app_url: {result}")

        logger.info("App uploaded → %s", app_url)
        self._app_url_cache[ipa_path] = app_url
        return app_url

    # ------------------------------------------------------------------
    # Device listing
    # ------------------------------------------------------------------

    async def list_ios_devices(self) -> list[Dict[str, Any]]:
        """Return available iOS devices from BrowserStack."""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                BS_DEVICES_URL,
                auth=self._auth,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    raise RuntimeError(f"BS devices list failed ({resp.status}): {body}")
                all_devices = await resp.json()

        ios_devices = [d for d in all_devices if d.get("os") == "ios"]
        logger.info("Found %d iOS devices on BrowserStack", len(ios_devices))
        return ios_devices

    # ------------------------------------------------------------------
    # Capability builder
    # ------------------------------------------------------------------

    def build_capabilities(
        self,
        app_url: str,
        device_name: str = "iPhone 14",
        os_version: str = "16",
        project_name: str = "Testara",
        build_name: str = "Cloud Run",
        session_name: str = "test",
        network_logs: bool = True,
        device_logs: bool = True,
    ) -> Dict[str, Any]:
        """
        Return a dict of BrowserStack capabilities to inject into the Appium harness.
        These map to the bstack:options block.
        """
        return {
            "userName":    self.username,
            "accessKey":   self.access_key,
            "deviceName":  device_name,
            "osVersion":   os_version,
            "app":         app_url,
            "projectName": project_name,
            "buildName":   build_name,
            "sessionName": session_name,
            "networkLogs": network_logs,
            "deviceLogs":  device_logs,
        }

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    async def validate_credentials(self) -> bool:
        """Ping BS API to verify credentials are valid."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://api-cloud.browserstack.com/app-automate/plan.json",
                    auth=self._auth,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    return resp.status == 200
        except Exception as e:
            logger.warning("BS credential check failed: %s", e)
            return False


def get_browserstack_service() -> Optional[BrowserStackService]:
    """
    Factory: returns a BrowserStackService if credentials are configured,
    otherwise returns None (local mode).
    """
    from app.core.config import settings
    if settings.browserstack_username and settings.browserstack_access_key:
        return BrowserStackService(
            username=settings.browserstack_username,
            access_key=settings.browserstack_access_key,
        )
    return None
