"""Appium-based test runner — subprocess isolated, timeout-safe.

Supports two execution modes:
  - local:  Appium server running on localhost (default)
  - cloud:  BrowserStack App Automate (set BS credentials in .env)
"""
import asyncio
import json
import logging
import signal
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, Literal, Optional

import aiohttp

try:
    from langsmith import traceable
except ImportError:
    def traceable(**kwargs):
        def decorator(fn): return fn
        return decorator

logger = logging.getLogger(__name__)

# Harness template written alongside test file; owns the Appium driver lifecycle.
# Uses double-braces {{ }} for literal braces in the f-string template.
_HARNESS_TEMPLATE = """\
import sys
import json
import traceback
import importlib.util
import io
import time as _time

try:
    from appium import webdriver as appium_webdriver
    from appium.options.ios import XCUITestOptions
except ImportError as e:
    print(json.dumps({{"success": False, "error": f"Import error: {{e}}", "logs": "", "duration": 0}}))
    sys.exit(2)

TEST_FILE       = {test_file!r}
BUNDLE_ID       = {bundle_id!r}
DEVICE_UDID     = {device_udid!r}
SERVER_URL      = {server_url!r}
LOGIN_EMAIL     = {login_email!r}
LOGIN_PASSWORD  = {login_password!r}

def _load_test_fn(path):
    spec = importlib.util.spec_from_file_location("_generated_test", path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    fns = [v for k, v in vars(mod).items() if k.startswith("test_") and callable(v)]
    if not fns:
        raise RuntimeError("No test_ function found in generated code")
    return fns[0]

def _auto_login(drv):
    if not LOGIN_EMAIL or not LOGIN_PASSWORD:
        return
    from appium.webdriver.common.appiumby import AppiumBy
    email_ids = ["emailTextField", "email_field", "usernameField", "email"]
    pwd_ids = ["passwordTextField", "password_field", "passwordField", "password"]
    btn_ids = ["loginButton", "login_button", "signInButton", "Log in"]
    for fid in email_ids:
        try:
            el = drv.find_element(AppiumBy.ACCESSIBILITY_ID, fid)
            if el.is_displayed():
                el.clear()
                el.send_keys(LOGIN_EMAIL)
                for pid in pwd_ids:
                    try:
                        pf = drv.find_element(AppiumBy.ACCESSIBILITY_ID, pid)
                        if pf.is_displayed():
                            pf.clear()
                            pf.send_keys(LOGIN_PASSWORD)
                            break
                    except Exception:
                        continue
                for bid in btn_ids:
                    try:
                        btn = drv.find_element(AppiumBy.ACCESSIBILITY_ID, bid)
                        if btn.is_displayed():
                            btn.click()
                            _time.sleep(3)
                            return
                    except Exception:
                        continue
                return
        except Exception:
            continue

start  = _time.time()
driver = None
try:
    test_fn = _load_test_fn(TEST_FILE)

    options = XCUITestOptions()
    options.bundle_id = BUNDLE_ID
    if DEVICE_UDID:
        options.udid = DEVICE_UDID
    options.automation_name = "XCUITest"
    options.no_reset = True

    driver = appium_webdriver.Remote(SERVER_URL, options=options)

    # Reset app to home screen before every test
    driver.terminate_app(BUNDLE_ID)
    _time.sleep(1)
    driver.activate_app(BUNDLE_ID)
    _time.sleep(2)

    # Auto-login if login screen is detected
    _auto_login(driver)

    _old_stdout = sys.stdout
    sys.stdout  = io.StringIO()
    try:
        test_fn(driver)
        _test_logs = sys.stdout.getvalue()
    finally:
        sys.stdout = _old_stdout

    duration = _time.time() - start
    print(json.dumps({{"success": True, "error": None, "logs": _test_logs, "duration": round(duration, 2)}}))
    sys.exit(0)

except AssertionError as e:
    duration = _time.time() - start
    screenshot_path = None
    if driver:
        try:
            ss_path = TEST_FILE.replace(".py", "_failure.png")
            driver.save_screenshot(ss_path)
            screenshot_path = ss_path
        except Exception:
            pass
    print(json.dumps({{
        "success": False,
        "error": f"Assertion failed: {{e}}",
        "logs": traceback.format_exc(),
        "duration": round(duration, 2),
        "screenshot": screenshot_path,
    }}))
    sys.exit(1)

except Exception as e:
    duration = _time.time() - start
    print(json.dumps({{
        "success": False,
        "error": f"{{type(e).__name__}}: {{e}}",
        "logs": traceback.format_exc(),
        "duration": round(duration, 2),
    }}))
    sys.exit(2)

finally:
    if driver:
        try:
            driver.quit()
        except Exception:
            pass
"""


_BS_HARNESS_TEMPLATE = """\
import sys
import json
import traceback
import importlib.util
import io
import time as _time

try:
    from appium import webdriver as appium_webdriver
    from appium.options.ios import XCUITestOptions
except ImportError as e:
    print(json.dumps({{"success": False, "error": f"Import error: {{e}}", "logs": "", "duration": 0}}))
    sys.exit(2)

TEST_FILE      = {test_file!r}
BS_USERNAME    = {bs_username!r}
BS_ACCESS_KEY  = {bs_access_key!r}
BS_APP_URL     = {bs_app_url!r}
DEVICE_NAME    = {device_name!r}
OS_VERSION     = {os_version!r}
BUILD_NAME     = {build_name!r}
SESSION_NAME   = {session_name!r}
LOGIN_EMAIL    = {login_email!r}
LOGIN_PASSWORD = {login_password!r}

SERVER_URL = "https://hub-cloud.browserstack.com/wd/hub"

def _load_test_fn(path):
    spec = importlib.util.spec_from_file_location("_generated_test", path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    fns = [v for k, v in vars(mod).items() if k.startswith("test_") and callable(v)]
    if not fns:
        raise RuntimeError("No test_ function found in generated code")
    return fns[0]

def _auto_login(drv):
    if not LOGIN_EMAIL or not LOGIN_PASSWORD:
        return
    from appium.webdriver.common.appiumby import AppiumBy
    email_ids = ["emailTextField", "email_field", "usernameField", "email"]
    pwd_ids   = ["passwordTextField", "password_field", "passwordField", "password"]
    btn_ids   = ["loginButton", "login_button", "signInButton", "Log in"]
    for fid in email_ids:
        try:
            el = drv.find_element(AppiumBy.ACCESSIBILITY_ID, fid)
            if el.is_displayed():
                el.clear(); el.send_keys(LOGIN_EMAIL)
                for pid in pwd_ids:
                    try:
                        pf = drv.find_element(AppiumBy.ACCESSIBILITY_ID, pid)
                        if pf.is_displayed():
                            pf.clear(); pf.send_keys(LOGIN_PASSWORD); break
                    except Exception: continue
                for bid in btn_ids:
                    try:
                        btn = drv.find_element(AppiumBy.ACCESSIBILITY_ID, bid)
                        if btn.is_displayed(): btn.click(); _time.sleep(3); return
                    except Exception: continue
                return
        except Exception: continue

start  = _time.time()
driver = None
try:
    test_fn = _load_test_fn(TEST_FILE)

    options = XCUITestOptions()
    options.set_capability("bstack:options", {{
        "userName":    BS_USERNAME,
        "accessKey":   BS_ACCESS_KEY,
        "deviceName":  DEVICE_NAME,
        "osVersion":   OS_VERSION,
        "app":         BS_APP_URL,
        "projectName": "Testara",
        "buildName":   BUILD_NAME,
        "sessionName": SESSION_NAME,
        "networkLogs": True,
        "deviceLogs":  True,
    }})
    options.automation_name = "XCUITest"
    options.no_reset = True

    driver = appium_webdriver.Remote(SERVER_URL, options=options)
    _auto_login(driver)

    _old_stdout = sys.stdout
    sys.stdout  = io.StringIO()
    try:
        test_fn(driver)
        _test_logs = sys.stdout.getvalue()
    finally:
        sys.stdout = _old_stdout

    duration = _time.time() - start
    print(json.dumps({{"success": True, "error": None, "logs": _test_logs, "duration": round(duration, 2)}}))
    sys.exit(0)

except AssertionError as e:
    duration = _time.time() - start
    print(json.dumps({{
        "success": False,
        "error": f"Assertion failed: {{e}}",
        "logs": traceback.format_exc(),
        "duration": round(duration, 2),
    }}))
    sys.exit(1)

except Exception as e:
    duration = _time.time() - start
    print(json.dumps({{
        "success": False,
        "error": f"{{type(e).__name__}}: {{e}}",
        "logs": traceback.format_exc(),
        "duration": round(duration, 2),
    }}))
    sys.exit(2)

finally:
    if driver:
        try: driver.quit()
        except Exception: pass
"""


class AppiumTestRunner:
    """Runs Appium Python tests in isolated subprocesses with timeout enforcement."""

    def __init__(
        self,
        recordings_dir: Path,
        bundle_id: str = "",
        server_url: str = "http://localhost:4723",
        test_timeout: int = 120,
    ):
        self.recordings_dir = Path(recordings_dir)
        self.recordings_dir.mkdir(parents=True, exist_ok=True)
        self.bundle_id = bundle_id
        self.server_url = server_url
        self.test_timeout = test_timeout

    @property
    def cloud_enabled(self) -> bool:
        from app.core.config import settings
        return bool(settings.browserstack_username and settings.browserstack_access_key)

    @traceable(name="execute-test")
    async def run_test(
        self,
        test_code: str,
        bundle_id: Optional[str] = None,
        device_udid: str = "",
        record_video: bool = False,
        execution_mode: Literal["local", "cloud"] = "local",
    ) -> Dict[str, Any]:
        """Run a generated Python Appium test in an isolated subprocess.

        Args:
            execution_mode: "local" uses local Appium server;
                            "cloud" uses BrowserStack App Automate.
                            Falls back to "local" if BS credentials are missing.
        """
        test_id = str(uuid.uuid4())
        effective_bundle_id = bundle_id or self.bundle_id

        # Route to cloud if requested and credentials are available
        use_cloud = execution_mode == "cloud" and self.cloud_enabled
        if execution_mode == "cloud" and not self.cloud_enabled:
            logger.warning("Cloud mode requested but BS credentials not configured — falling back to local")

        if use_cloud:
            return await self._run_test_cloud(test_code, test_id)

        # ── Local execution ───────────────────────────────────────────────────
        if not effective_bundle_id:
            return {
                "success": False,
                "test_id": test_id,
                "error": "bundle_id is required. Set BUNDLE_ID in .env or pass it in the request.",
                "logs": "",
                "duration": 0,
            }

        # Pre-check: is Appium server reachable?
        if not await self._is_server_running():
            return {
                "success": False,
                "test_id": test_id,
                "error": f"Appium server not reachable at {self.server_url}. Start it with: appium",
                "logs": "",
                "duration": 0,
            }

        logger.info("=== Appium test run %s (local) ===", test_id)
        logger.info("  bundle_id=%s  udid=%s  server=%s", effective_bundle_id, device_udid or "auto", self.server_url)

        run_dir  = Path(tempfile.mkdtemp(prefix=f"testara_{test_id}_"))
        test_file    = run_dir / "test_generated.py"
        harness_file = run_dir / "harness.py"
        video_path   = self.recordings_dir / f"{test_id}.mp4"

        try:
            test_file.write_text(test_code)
            from app.core.config import settings
            harness_src = _HARNESS_TEMPLATE.format(
                test_file=str(test_file),
                bundle_id=effective_bundle_id,
                device_udid=device_udid,
                server_url=self.server_url,
                login_email=settings.test_credentials_email or "",
                login_password=settings.test_credentials_password or "",
            )
            harness_file.write_text(harness_src)

            recording_proc = None
            if record_video:
                recording_proc = await self._start_recording(device_udid, video_path)

            result = await self._run_harness(harness_file)

            if recording_proc:
                await self._stop_recording(recording_proc)

            video_ready = record_video and video_path.exists() and video_path.stat().st_size > 0

            # Copy failure screenshot to recordings dir so it persists after temp cleanup
            screenshot_name = None
            raw_screenshot = result.get("screenshot")
            if raw_screenshot and Path(raw_screenshot).exists():
                screenshot_name = f"{test_id}_failure.png"
                import shutil as _shutil
                _shutil.copy2(raw_screenshot, self.recordings_dir / screenshot_name)

            return {
                "test_id":        test_id,
                "execution_mode": "local",
                "success":        result.get("success", False),
                "logs":           result.get("logs", ""),
                "duration":       result.get("duration", 0),
                "error":          result.get("error"),
                "screenshot":     screenshot_name,
                "video_path":     str(video_path.name) if video_ready else None,
            }

        except Exception as e:
            logger.error("Test run %s failed: %s", test_id, e, exc_info=True)
            return {"test_id": test_id, "success": False, "error": str(e), "logs": "", "duration": 0}

        finally:
            shutil.rmtree(run_dir, ignore_errors=True)

    async def _run_test_cloud(self, test_code: str, test_id: str) -> Dict[str, Any]:
        """Run test on BrowserStack App Automate."""
        from app.core.config import settings
        from app.services.browserstack_service import BrowserStackService

        logger.info("=== Appium test run %s (BrowserStack cloud) ===", test_id)

        # Resolve app URL: use pre-configured bs:// URL or upload IPA now
        app_url = settings.browserstack_app_url
        if not app_url:
            if not settings.browserstack_ipa_path:
                return {
                    "test_id": test_id,
                    "success": False,
                    "error": (
                        "Cloud execution requires either BROWSERSTACK_APP_URL (bs:// URL from prior upload) "
                        "or BROWSERSTACK_IPA_PATH pointing to a .ipa file."
                    ),
                    "logs": "",
                    "duration": 0,
                }
            bs = BrowserStackService(settings.browserstack_username, settings.browserstack_access_key)
            app_url = await bs.upload_app(settings.browserstack_ipa_path, custom_id="testara-app")

        run_dir      = Path(tempfile.mkdtemp(prefix=f"testara_{test_id}_"))
        test_file    = run_dir / "test_generated.py"
        harness_file = run_dir / "harness.py"

        try:
            test_file.write_text(test_code)
            harness_src = _BS_HARNESS_TEMPLATE.format(
                test_file=str(test_file),
                bs_username=settings.browserstack_username,
                bs_access_key=settings.browserstack_access_key,
                bs_app_url=app_url,
                device_name=settings.browserstack_device,
                os_version=settings.browserstack_os_version,
                build_name="Testara Cloud",
                session_name=test_id,
                login_email=settings.test_credentials_email or "",
                login_password=settings.test_credentials_password or "",
            )
            harness_file.write_text(harness_src)

            # Cloud sessions need extra time for device allocation + app install
            cloud_timeout = max(self.test_timeout, 300)
            original_timeout = self.test_timeout
            self.test_timeout = cloud_timeout
            try:
                result = await self._run_harness(harness_file)
            finally:
                self.test_timeout = original_timeout

            return {
                "test_id":        test_id,
                "execution_mode": "cloud",
                "provider":       "browserstack",
                "device":         settings.browserstack_device,
                "os_version":     settings.browserstack_os_version,
                "success":        result.get("success", False),
                "logs":           result.get("logs", ""),
                "duration":       result.get("duration", 0),
                "error":          result.get("error"),
            }

        except Exception as e:
            logger.error("Cloud test run %s failed: %s", test_id, e, exc_info=True)
            return {"test_id": test_id, "success": False, "error": str(e), "logs": "", "duration": 0}

        finally:
            shutil.rmtree(run_dir, ignore_errors=True)

    async def _is_server_running(self) -> bool:
        """Quick health check against Appium /status endpoint."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.server_url}/status", timeout=aiohttp.ClientTimeout(total=3)
                ) as resp:
                    return resp.status == 200
        except Exception:
            return False

    async def _run_harness(self, harness_file: Path) -> Dict[str, Any]:
        """Run harness.py as subprocess, parse JSON from stdout."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "python", str(harness_file),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=self.test_timeout
                )
            except asyncio.TimeoutError:
                logger.error("Harness timed out after %ds", self.test_timeout)
                proc.kill()
                await proc.wait()
                return {"success": False, "error": f"Test timed out after {self.test_timeout}s", "logs": "", "duration": self.test_timeout}

            raw_stdout = stdout.decode(errors="replace").strip()
            raw_stderr = stderr.decode(errors="replace").strip()
            if raw_stderr:
                logger.debug("Harness stderr:\n%s", raw_stderr)

            try:
                return json.loads(raw_stdout)
            except (json.JSONDecodeError, ValueError):
                logger.error("Harness non-JSON stdout: %r", raw_stdout[:500])
                return {
                    "success": False,
                    "error": raw_stderr or "Harness crashed before producing output",
                    "logs": raw_stdout,
                    "duration": 0,
                    "exit_code": proc.returncode,
                }
        except Exception as e:
            return {"success": False, "error": str(e), "logs": "", "duration": 0}

    async def _start_recording(self, device_udid: str, output_path: Path) -> Optional[Any]:
        if not device_udid:
            logger.warning("No device_udid — skipping video recording")
            return None
        try:
            proc = await asyncio.create_subprocess_exec(
                "xcrun", "simctl", "io", device_udid, "recordVideo", str(output_path),
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            )
            await asyncio.sleep(2)
            if proc.returncode is not None:
                logger.warning("Recording process exited early")
                return None
            logger.info("Video recording started → %s", output_path)
            return proc
        except Exception as e:
            logger.warning("Could not start video recording: %s", e)
            return None

    async def _stop_recording(self, proc) -> None:
        try:
            if proc and proc.returncode is None:
                proc.send_signal(signal.SIGINT)
                try:
                    await asyncio.wait_for(proc.wait(), timeout=10.0)
                except asyncio.TimeoutError:
                    proc.kill()
                    await proc.wait()
                await asyncio.sleep(1)
        except Exception as e:
            logger.warning("Error stopping recording: %s", e)


# Backwards-compat alias
TestRunner = AppiumTestRunner
