"""iOS Simulator test runner with video recording"""
import asyncio
import logging
import re
import signal
import subprocess
import tempfile
import time
import uuid
from pathlib import Path
from typing import Dict, Any, Optional
import os

logger = logging.getLogger(__name__)


class TestRunner:
    """Runs XCUITests in iOS Simulator and records video"""

    def __init__(self, recordings_dir: Path, xcode_project: str = "", xcode_scheme: str = "SampleApp", xcode_ui_test_target: str = "SampleAppUITests"):
        self.recordings_dir = Path(recordings_dir)
        self.recordings_dir.mkdir(parents=True, exist_ok=True)
        self.xcode_project = xcode_project
        self.xcode_scheme = xcode_scheme
        self.xcode_ui_test_target = xcode_ui_test_target
    
    def _is_udid(self, device_str: str) -> bool:
        """Check if string is a valid UDID (UUID format)"""
        return len(device_str) == 36 and device_str.count('-') == 4
    
    async def run_test(
        self,
        test_code: str,
        app_name: str = "YourApp",
        device: str = "iPhone 15 Pro",
        ios_version: str = "17.0"
    ) -> Dict[str, Any]:
        """
        Run a test in the simulator and record video.
        
        Args:
            test_code: Swift XCUITest code
            app_name: Name of the app to test
            device: Simulator device name OR UDID (if it's a valid UUID)
            ios_version: iOS version
            
        Returns:
            Dict with test results, video path, logs
        """
        test_id = str(uuid.uuid4())
        video_path = self.recordings_dir / f"{test_id}.mp4"

        logger.info(f"=== Starting test run {test_id} ===")
        logger.info(f"  Device: {device}, iOS: {ios_version}, App: {app_name}")
        logger.info(f"  Xcode project: {self.xcode_project}")
        logger.info(f"  Scheme: {self.xcode_scheme}, UI test target: {self.xcode_ui_test_target}")
        logger.info(f"  Test code length: {len(test_code)} chars")

        try:
            # 1. Create temporary test file
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.swift',
                delete=False,
                dir=tempfile.gettempdir()
            ) as f:
                f.write(test_code)
                test_file_path = f.name
            logger.info(f"  Temp test file: {test_file_path}")

            # 2. Get simulator UDID (or use if already a UDID)
            if self._is_udid(device):
                device_id = device
                logger.info(f"Using device UDID directly: {device_id}")
            else:
                logger.info(f"Looking up simulator UDID for '{device}' (iOS {ios_version})")
                device_id = await self._get_simulator_udid(device, ios_version)
                if not device_id:
                    logger.error(f"Simulator not found: '{device}' (iOS {ios_version})")
                    return {
                        "success": False,
                        "error": f"Simulator '{device} ({ios_version})' not found",
                        "test_id": test_id
                    }
            
            # 3. Boot simulator
            await self._boot_simulator(device_id)

            # 4. Ensure Simulator app is open (required for video recording)
            await self._bring_simulator_to_front(device_id)
            # Extra wait for Simulator GUI to fully connect
            await asyncio.sleep(3)

            # 5. Start video recording (non-fatal if it fails)
            recording_process = None
            try:
                recording_process = await self._start_recording(device_id, video_path)
            except Exception as e:
                logger.warning(f"Video recording failed to start (continuing without): {e}")

            # 6. Run the test
            test_result = await self._execute_test(test_file_path, device_id, app_name)

            # 7. Stop recording
            if recording_process:
                await self._stop_recording(recording_process)

            # 8. Verify video file exists and has content
            video_ready = False
            if video_path.exists():
                file_size = video_path.stat().st_size
                if file_size > 0:
                    logger.info(f"Video file created successfully: {file_size} bytes")
                    video_ready = True
                else:
                    logger.warning(f"Video file exists but is empty: {video_path}")
            else:
                logger.info("No video file (recording was skipped or failed)")
            
            # 9. Clean up temp file
            os.unlink(test_file_path)
            
            return {
                "success": test_result["success"],
                "test_id": test_id,
                "video_path": str(video_path.name) if video_ready else None,
                "logs": test_result.get("logs", ""),
                "duration": test_result.get("duration", 0),
                "device": device,
                "ios_version": ios_version
            }
            
        except Exception as e:
            logger.error(f"Test execution failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "test_id": test_id
            }
    
    async def _get_simulator_udid(self, device: str, ios_version: str) -> Optional[str]:
        """Get simulator UDID for the specified device and iOS version"""
        try:
            result = await asyncio.create_subprocess_exec(
                'xcrun', 'simctl', 'list', 'devices', 'available',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await result.communicate()
            
            # Parse output to find matching device
            output = stdout.decode()
            lines = output.split('\n')
            
            current_runtime = None
            for line in lines:
                if '-- iOS' in line or '-- com.apple.CoreSimulator.SimRuntime.iOS' in line:
                    # Extract iOS version from runtime line
                    if ios_version.replace('.', '-') in line:
                        current_runtime = ios_version
                elif current_runtime and device in line and '(Booted)' not in line:
                    # Extract UDID from device line
                    if '(' in line and ')' in line:
                        udid = line.split('(')[1].split(')')[0]
                        if len(udid) == 36:  # UUID format
                            return udid
            
            # Fallback: get any available device
            result = await asyncio.create_subprocess_exec(
                'xcrun', 'simctl', 'list', 'devices', 'available', '--json',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await result.communicate()
            
            import json
            data = json.loads(stdout.decode())
            
            for runtime, devices in data.get('devices', {}).items():
                for dev in devices:
                    if device in dev.get('name', '') and dev.get('isAvailable'):
                        return dev['udid']
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get simulator UDID: {e}")
            return None
    
    async def _boot_simulator(self, device_id: str):
        """Boot the simulator if not already booted"""
        try:
            # Check current state of all simulators
            result = await asyncio.create_subprocess_exec(
                'xcrun', 'simctl', 'list', 'devices', '--json',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()

            import json
            try:
                data = json.loads(stdout.decode())
                # Find our device and log its state
                for runtime, devices in data.get('devices', {}).items():
                    for dev in devices:
                        if dev.get('udid') == device_id:
                            logger.info(f"Simulator state: name={dev.get('name')}, "
                                        f"state={dev.get('state')}, "
                                        f"runtime={runtime}, "
                                        f"available={dev.get('isAvailable')}")
                            if dev.get('state') == 'Booted':
                                logger.info(f"Simulator {device_id} already booted")
                                return
                            break
            except json.JSONDecodeError:
                logger.warning("Could not parse simctl JSON, falling back to text check")
                output = stdout.decode()
                if '(Booted)' in output and device_id in output:
                    logger.info(f"Simulator {device_id} already booted (text check)")
                    return

            # Boot simulator
            logger.info(f"Booting simulator {device_id}...")
            result = await asyncio.create_subprocess_exec(
                'xcrun', 'simctl', 'boot', device_id,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            if result.returncode != 0:
                err = stderr.decode()
                if 'Unable to boot device in current state: Booted' in err:
                    logger.info("Simulator was already booted (race condition)")
                else:
                    logger.error(f"simctl boot failed (rc={result.returncode}): {err}")
                    raise RuntimeError(f"Failed to boot simulator: {err}")
            else:
                logger.info("simctl boot succeeded, waiting for startup...")

            # Wait for boot to complete
            await asyncio.sleep(3)
            logger.info("Simulator boot wait complete")

            # Force English locale on the simulator to prevent keyboard language switching
            for key, value in [("AppleLanguages", "-array en"), ("AppleLocale", "-string en_US")]:
                await asyncio.create_subprocess_exec(
                    'xcrun', 'simctl', 'spawn', device_id,
                    'defaults', 'write', 'com.apple.Preferences', key, *value.split(),
                    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
                )

        except Exception as e:
            logger.error(f"Failed to boot simulator: {e}", exc_info=True)
            raise
    
    async def _start_recording(self, device_id: str, output_path: Path):
        """Start video recording of the simulator"""
        try:
            logger.info(f"Starting video recording to {output_path}")
            process = await asyncio.create_subprocess_exec(
                'xcrun', 'simctl', 'io', device_id, 'recordVideo',
                str(output_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Give recording time to start
            await asyncio.sleep(2)
            
            # Check if process is still running
            if process.returncode is not None:
                stdout, stderr = await process.communicate()
                logger.error(f"Recording failed to start. stdout: {stdout.decode()}, stderr: {stderr.decode()}")
                raise RuntimeError(f"Recording process exited immediately: {stderr.decode()}")
            
            logger.info("Recording process started successfully")
            return process
            
        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            raise
    
    async def _stop_recording(self, process):
        """Stop video recording. Must use SIGINT so simctl finalizes the file."""
        try:
            if process and process.returncode is None:
                logger.info("Stopping video recording with SIGINT")
                process.send_signal(signal.SIGINT)

                # Wait for process to finalize the video
                try:
                    await asyncio.wait_for(process.wait(), timeout=10.0)
                except asyncio.TimeoutError:
                    logger.warning("Recording process didn't terminate, killing it")
                    process.kill()
                    await process.wait()

                # Give extra time for file to be fully written
                await asyncio.sleep(1)
                logger.info("Recording process terminated, file should be ready")
                
        except Exception as e:
            logger.error(f"Failed to stop recording: {e}")
    
    def _extract_class_name(self, test_code: str) -> Optional[str]:
        """Extract the XCTestCase class name from Swift code."""
        match = re.search(r'(?:final\s+)?class\s+(\w+)\s*:\s*XCTestCase', test_code)
        return match.group(1) if match else None

    async def _terminate_running_apps(self, device_id: str):
        """Terminate user apps on the simulator to ensure a clean state before testing."""
        try:
            logger.info("Terminating running apps on simulator for clean state...")
            # Get the bundle ID from the Xcode project's build settings
            proc = await asyncio.create_subprocess_exec(
                'xcodebuild', '-project', self.xcode_project,
                '-scheme', self.xcode_scheme,
                '-showBuildSettings',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            output = stdout.decode(errors='replace')

            bundle_id = None
            for line in output.splitlines():
                if 'PRODUCT_BUNDLE_IDENTIFIER' in line:
                    bundle_id = line.split('=', 1)[1].strip()
                    break

            if bundle_id:
                logger.info(f"Terminating app with bundle ID: {bundle_id}")
                proc = await asyncio.create_subprocess_exec(
                    'xcrun', 'simctl', 'terminate', device_id, bundle_id,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await proc.communicate()
                # Small delay to let the app fully terminate
                await asyncio.sleep(1)
            else:
                logger.warning("Could not determine bundle ID, skipping app termination")
        except Exception as e:
            logger.warning(f"Failed to terminate running apps (non-fatal): {e}")

    async def _bring_simulator_to_front(self, device_id: str):
        """Bring the Simulator app to the foreground (needed for video recording)."""
        try:
            logger.info(f"Bringing simulator {device_id} to foreground...")
            proc = await asyncio.create_subprocess_exec(
                'open', '-a', 'Simulator', '--args', '-CurrentDeviceUDID', device_id,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode != 0:
                logger.warning(f"open -a Simulator returned {proc.returncode}: {stderr.decode()}")
            await asyncio.sleep(1)

            proc = await asyncio.create_subprocess_exec(
                'osascript', '-e', 'tell application "Simulator" to activate',
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode != 0:
                logger.warning(f"osascript activate returned {proc.returncode}: {stderr.decode()}")
            await asyncio.sleep(1)
            logger.info("Simulator brought to foreground")
        except Exception as e:
            logger.warning(f"Could not bring simulator to front: {e}")

    async def _build_for_testing(self, device_id: str) -> tuple:
        """Run xcodebuild build-for-testing (incremental)."""
        cmd = [
            'xcodebuild', 'build-for-testing',
            '-project', self.xcode_project,
            '-scheme', self.xcode_scheme,
            '-destination', f'platform=iOS Simulator,id={device_id}',
            '-quiet',
        ]
        logger.info(f"Build command: {' '.join(cmd)}")
        build_start = time.time()
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        try:
            stdout, _ = await asyncio.wait_for(process.communicate(), timeout=180)
        except asyncio.TimeoutError:
            process.kill()
            logger.error("Build timed out after 3 minutes")
            return False, "Build timed out after 3 minutes"
        output = stdout.decode(errors='replace')
        build_duration = time.time() - build_start
        logger.info(f"Build finished in {build_duration:.1f}s, returncode={process.returncode}")
        if process.returncode != 0:
            logger.error(f"Build failed output (last 1000 chars): {output[-1000:]}")
        return process.returncode == 0, output

    async def _execute_test(
        self,
        test_file: str,
        device_id: str,
        app_name: str
    ) -> Dict[str, Any]:
        """Execute XCUITest code on the simulator using xcodebuild."""
        start_time = time.time()

        if not self.xcode_project:
            return {
                "success": False,
                "logs": "XCODE_PROJECT not configured. Set it in .env.",
                "duration": 0,
            }

        project_path = Path(self.xcode_project)
        if not project_path.exists():
            return {
                "success": False,
                "logs": f"Xcode project not found: {self.xcode_project}",
                "duration": 0,
            }

        # Read the test code to extract class name and method name
        with open(test_file) as f:
            test_code = f.read()

        class_name = self._extract_class_name(test_code)
        if not class_name:
            logger.error(f"Could not extract XCTestCase class name from code:\n{test_code[:500]}")
            return {
                "success": False,
                "logs": "Could not extract XCTestCase class name from generated code",
                "duration": 0,
            }

        test_method = self._extract_test_method(test_code)
        logger.info(f"Extracted class={class_name}, method={test_method}")

        # Write to LLMGeneratedTest.swift — the file already included in the Xcode target
        ui_tests_dir = project_path.parent / self.xcode_ui_test_target
        dest_file = ui_tests_dir / "LLMGeneratedTest.swift"
        logger.info(f"Writing test to {dest_file}")
        logger.info(f"UI tests dir exists: {ui_tests_dir.exists()}, contents: {list(ui_tests_dir.iterdir()) if ui_tests_dir.exists() else 'N/A'}")
        dest_file.write_text(test_code)
        logger.info(f"Test file written: {dest_file.stat().st_size} bytes")

        try:
            # Step 0: Terminate any running app to ensure clean state
            await self._terminate_running_apps(device_id)

            # Step 1: Build for testing (incremental)
            logger.info("Building project for testing...")
            build_ok, build_output = await self._build_for_testing(device_id)
            if not build_ok:
                logger.error("Build failed")
                return {
                    "success": False,
                    "logs": f"BUILD FAILED:\n{build_output[-3000:]}",
                    "duration": time.time() - start_time,
                }
            logger.info("Build succeeded")

            # Step 2: Bring simulator to front for video capture
            await self._bring_simulator_to_front(device_id)

            # Step 3: Run the test
            only_testing = f'{self.xcode_ui_test_target}/{class_name}'
            if test_method:
                only_testing += f'/{test_method}'

            cmd = [
                'xcodebuild', 'test',
                '-project', self.xcode_project,
                '-scheme', self.xcode_scheme,
                '-destination', f'id={device_id}',
                f'-only-testing:{only_testing}',
                '-parallel-testing-enabled', 'NO',
                '-maximum-concurrent-test-simulator-destinations', '1',
                '-testLanguage', 'en',
                '-testRegion', 'en_US',
            ]

            logger.info(f"Running: {' '.join(cmd)}")

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )

            try:
                stdout, _ = await asyncio.wait_for(process.communicate(), timeout=120)
            except asyncio.TimeoutError:
                process.kill()
                return {
                    "success": False,
                    "logs": "Test execution timed out after 120 seconds",
                    "duration": time.time() - start_time,
                }

            logs = stdout.decode(errors='replace')
            duration = time.time() - start_time

            success = '** TEST SUCCEEDED **' in logs
            if '** TEST FAILED **' in logs:
                success = False

            logger.info(f"Test {'PASSED' if success else 'FAILED'} in {duration:.1f}s")
            logger.info(f"xcodebuild returncode={process.returncode}")
            # Log last 500 chars of output for quick debugging
            logger.debug(f"Test output tail:\n{logs[-500:]}")

            return {
                "success": success,
                "logs": logs[-5000:],
                "duration": duration,
            }

        except Exception as e:
            logger.error(f"Test execution failed: {e}")
            return {
                "success": False,
                "logs": str(e),
                "duration": time.time() - start_time,
            }

    @staticmethod
    def _extract_test_method(test_code: str) -> Optional[str]:
        """Extract the test method name from Swift code."""
        match = re.search(r'func (test\w+)\(\)', test_code)
        return match.group(1) if match else None
