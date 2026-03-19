"""Appium-based test runner — subprocess isolated, timeout-safe."""
import asyncio
import json
import logging
import signal
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

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
    from appium.options import XCUITestOptions
except ImportError as e:
    print(json.dumps({{"success": False, "error": f"Import error: {{e}}", "logs": "", "duration": 0}}))
    sys.exit(2)

TEST_FILE   = {test_file!r}
BUNDLE_ID   = {bundle_id!r}
DEVICE_UDID = {device_udid!r}
SERVER_URL  = {server_url!r}

def _load_test_fn(path):
    spec = importlib.util.spec_from_file_location("_generated_test", path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    fns = [v for k, v in vars(mod).items() if k.startswith("test_") and callable(v)]
    if not fns:
        raise RuntimeError("No test_ function found in generated code")
    return fns[0]

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

    async def run_test(
        self,
        test_code: str,
        bundle_id: Optional[str] = None,
        device_udid: str = "",
        record_video: bool = False,
    ) -> Dict[str, Any]:
        """Run a generated Python Appium test in an isolated subprocess."""
        test_id = str(uuid.uuid4())
        effective_bundle_id = bundle_id or self.bundle_id

        if not effective_bundle_id:
            return {
                "success": False,
                "test_id": test_id,
                "error": "bundle_id is required. Set BUNDLE_ID in .env or pass it in the request.",
                "logs": "",
                "duration": 0,
            }

        logger.info("=== Appium test run %s ===", test_id)
        logger.info("  bundle_id=%s  udid=%s  server=%s", effective_bundle_id, device_udid or "auto", self.server_url)

        run_dir  = Path(tempfile.mkdtemp(prefix=f"testara_{test_id}_"))
        test_file    = run_dir / "test_generated.py"
        harness_file = run_dir / "harness.py"
        video_path   = self.recordings_dir / f"{test_id}.mp4"

        try:
            test_file.write_text(test_code)
            harness_src = _HARNESS_TEMPLATE.format(
                test_file=str(test_file),
                bundle_id=effective_bundle_id,
                device_udid=device_udid,
                server_url=self.server_url,
            )
            harness_file.write_text(harness_src)

            recording_proc = None
            if record_video:
                recording_proc = await self._start_recording(device_udid, video_path)

            result = await self._run_harness(harness_file)

            if recording_proc:
                await self._stop_recording(recording_proc)

            video_ready = record_video and video_path.exists() and video_path.stat().st_size > 0

            return {
                "test_id":    test_id,
                "success":    result.get("success", False),
                "logs":       result.get("logs", ""),
                "duration":   result.get("duration", 0),
                "error":      result.get("error"),
                "screenshot": result.get("screenshot"),
                "video_path": str(video_path.name) if video_ready else None,
            }

        except Exception as e:
            logger.error("Test run %s failed: %s", test_id, e, exc_info=True)
            return {"test_id": test_id, "success": False, "error": str(e), "logs": "", "duration": 0}

        finally:
            shutil.rmtree(run_dir, ignore_errors=True)

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
