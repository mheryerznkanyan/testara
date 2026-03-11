#!/usr/bin/env python3
"""
iOS Test Automator - Streamlit UI

A user-friendly interface for generating and running iOS UI tests using natural language descriptions.
"""

import streamlit as st
import requests
import subprocess
import json
import time
import os
import re
import signal
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Test history persistence helpers
# ---------------------------------------------------------------------------

_HISTORY_FILE = Path(__file__).resolve().parent / "test_history.json"


def _serialize_history(history: list) -> list:
    """Convert datetime objects to ISO strings for JSON serialisation."""
    out = []
    for item in history:
        entry = dict(item)
        if isinstance(entry.get("timestamp"), datetime):
            entry["timestamp"] = entry["timestamp"].isoformat()
        out.append(entry)
    return out


def _deserialize_history(raw: list) -> list:
    """Convert ISO timestamp strings back to datetime objects."""
    out = []
    for item in raw:
        entry = dict(item)
        if isinstance(entry.get("timestamp"), str):
            try:
                entry["timestamp"] = datetime.fromisoformat(entry["timestamp"])
            except ValueError:
                pass
        out.append(entry)
    return out


def load_history() -> list:
    """Load test history from the JSON file, returning an empty list on error."""
    if _HISTORY_FILE.exists():
        try:
            return _deserialize_history(json.loads(_HISTORY_FILE.read_text("utf-8")))
        except Exception:
            pass
    return []


def save_history(history: list) -> None:
    """Persist test history to the JSON file (best-effort)."""
    try:
        _HISTORY_FILE.write_text(
            json.dumps(_serialize_history(history), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception:
        pass

# Load .env from project root
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Use env var or sidebar input — no hardcoded machine paths
PROJECT_ROOT = os.getenv("PROJECT_ROOT", "")
if not PROJECT_ROOT:
    PROJECT_ROOT = st.sidebar.text_input(
        "Project Root Path",
        value="",
        placeholder="/path/to/iOS-test-automator",
    )
PROJECT_DIR = PROJECT_ROOT
XCODE_PROJECT = f"{PROJECT_DIR}/SampleApp.xcodeproj"
XCODE_SCHEME = "SampleApp"
TEST_TARGET = "SampleAppUITests"
# Save to LLMGeneratedTest.swift - the file that's included in the Xcode project
TEST_FILE = f"{PROJECT_DIR}/SampleAppUITests/LLMGeneratedTest.swift"
RECORDINGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "recordings")

# Simulator configuration - will be detected dynamically
SIMULATOR_NAME = os.getenv("SIMULATOR_NAME", "iPhone 17")

# Initialize session state — load persisted history on first run
if "test_history" not in st.session_state:
    st.session_state.test_history = load_history()
if "current_test" not in st.session_state:
    st.session_state.current_test = None

# Create recordings directory
os.makedirs(RECORDINGS_DIR, exist_ok=True)

def sanitize_class_name(name: str) -> str:
    """Convert test description to valid Swift class name"""
    # Remove special characters and convert to CamelCase
    words = re.findall(r'\w+', name)
    return ''.join(word.capitalize() for word in words) + 'Test'

def get_simulator_id(simulator_name: str) -> str:
    """Get simulator ID from name"""
    try:
        result = subprocess.run(
            ["xcrun", "simctl", "list", "devices"],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Extract UUID for the specified device
        pattern = rf'{simulator_name}.*?([A-F0-9-]{{36}})'
        match = re.search(pattern, result.stdout)

        if match:
            return match.group(1)
        return None
    except Exception as e:
        st.error(f"Failed to get simulator ID: {str(e)}")
        return None

def is_simulator_booted(simulator_id: str) -> bool:
    """Check if the simulator is already booted"""
    try:
        result = subprocess.run(
            ["xcrun", "simctl", "list", "devices", "-j"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            devices = json.loads(result.stdout)
            for runtime, device_list in devices.get("devices", {}).items():
                for device in device_list:
                    if device.get("udid") == simulator_id:
                        return device.get("state") == "Booted"
        return False
    except Exception:
        return False

def boot_simulator(simulator_id: str) -> bool:
    """Boot the iOS simulator (skips if already booted)"""
    try:
        # Check if already booted - skip shutdown/boot if so
        if is_simulator_booted(simulator_id):
            st.info("Simulator already booted, reusing...")
            # Just bring to front
            subprocess.run(
                ["open", "-a", "Simulator", "--args", "-CurrentDeviceUDID", simulator_id],
                capture_output=True,
                timeout=10
            )
            time.sleep(1)
            subprocess.run(
                ["osascript", "-e", 'tell application "Simulator" to activate'],
                capture_output=True,
                timeout=5
            )
            time.sleep(1)
            return True

        # Only shutdown if we need to boot a different simulator
        subprocess.run(
            ["xcrun", "simctl", "shutdown", "all"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10
        )
        time.sleep(1)

        # Boot the target simulator
        boot_result = subprocess.run(
            ["xcrun", "simctl", "boot", simulator_id],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Check if already booted (this is OK)
        if boot_result.returncode != 0 and "Unable to boot device in current state: Booted" not in boot_result.stderr:
            st.error(f"Failed to boot simulator: {boot_result.stderr}")
            return False

        # Open Simulator app with specific device
        subprocess.run(
            ["open", "-a", "Simulator", "--args", "-CurrentDeviceUDID", simulator_id],
            capture_output=True,
            timeout=10
        )
        time.sleep(3)

        # Bring Simulator to front
        subprocess.run(
            ["osascript", "-e", 'tell application "Simulator" to activate'],
            capture_output=True,
            timeout=5
        )
        time.sleep(2)

        return True
    except Exception as e:
        st.error(f"Failed to boot simulator: {str(e)}")
        return False

def generate_test(description: str, class_name: str) -> dict:
    """Call the backend RAG endpoint to generate test code"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/generate-test-with-rag",
            json={
                "test_description": description,
                "class_name": class_name
            },
            timeout=60
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Failed to generate test: {str(e)}")
        return None

def save_test_file(swift_code: str, class_name: str) -> str:
    """Save generated test to LLMGeneratedTest.swift (the file included in Xcode project)"""
    try:
        with open(TEST_FILE, 'w') as f:
            f.write(swift_code)
        return TEST_FILE
    except Exception as e:
        st.error(f"Failed to save test file: {str(e)}")
        return None

def build_for_testing(simulator_id: str, clean_build: bool = False) -> tuple[bool, str]:
    """Build the project for testing (incremental by default)"""
    try:
        # Use incremental build by default - much faster
        if clean_build:
            cmd = [
                "xcodebuild",
                "clean", "build-for-testing",
                "-project", XCODE_PROJECT,
                "-scheme", XCODE_SCHEME,
                "-destination", f"platform=iOS Simulator,id={simulator_id}",
                "-quiet"
            ]
        else:
            # Incremental build - only rebuilds changed files
            cmd = [
                "xcodebuild",
                "build-for-testing",
                "-project", XCODE_PROJECT,
                "-scheme", XCODE_SCHEME,
                "-destination", f"platform=iOS Simulator,id={simulator_id}",
                "-quiet"
            ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180
        )

        output = result.stdout + result.stderr
        success = result.returncode == 0

        return success, output
    except subprocess.TimeoutExpired:
        return False, "Build timed out after 3 minutes"
    except Exception as e:
        return False, f"Failed to build: {str(e)}"

def extract_test_method_name(swift_code: str) -> str:
    """Extract test method name from Swift code"""
    match = re.search(r'func (test\w+)\(\)', swift_code)
    if match:
        return match.group(1)
    return "testExample"

def extract_class_name_from_code(swift_code: str) -> str:
    """Extract actual class name from Swift code"""
    match = re.search(r'(?:final\s+)?class\s+(\w+)\s*:', swift_code)
    if match:
        return match.group(1)
    return None

def run_xcode_test(class_name: str, swift_code: str, simulator_id: str, record_video: bool = True) -> tuple[bool, str, str]:
    """Run the generated test using xcodebuild with optional video recording"""
    recording_path = None
    recording_process = None

    try:
        # Extract test method name first
        test_method = extract_test_method_name(swift_code)

        # Start video recording if requested
        if record_video:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # Save recordings to project root like the shell script does
            recording_path = f"{PROJECT_ROOT}/test_recording_{class_name}_{timestamp}.mp4"

            if os.path.exists(recording_path):
                os.remove(recording_path)

            st.info(f"Starting video recording on simulator: {simulator_id[:8]}...")

            recording_process = subprocess.Popen(
                ["xcrun", "simctl", "io", simulator_id, "recordVideo", recording_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            time.sleep(3)

            # Bring simulator to front - critical for recording to capture the app
            subprocess.run(
                ["osascript", "-e", 'tell application "Simulator" to activate'],
                capture_output=True,
                timeout=5
            )
            time.sleep(2)

        # Build command - exactly like bash script
        cmd = [
            "xcodebuild",
            "test",
            "-project", XCODE_PROJECT,
            "-scheme", XCODE_SCHEME,
            "-destination", f"id={simulator_id}",
            f"-only-testing:{TEST_TARGET}/{class_name}/{test_method}",
            "-parallel-testing-enabled", "NO",
            "-maximum-concurrent-test-simulator-destinations", "1",
            # Force English locale so the simulator never switches to the
            # system keyboard language (e.g. Armenian) mid-test.
            "-testLanguage", "en",
            "-testRegion", "en_US",
        ]

        st.info(f"Running test: {class_name}/{test_method} on simulator {simulator_id[:8]}...")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )

        # Wait for any final UI updates before stopping recording (like shell script)
        time.sleep(3)

        # Stop recording gracefully
        if recording_process:
            st.info("Stopping video recording...")
            recording_process.send_signal(signal.SIGINT)
            time.sleep(2)
            try:
                recording_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                recording_process.kill()

        output = result.stdout + result.stderr
        success = result.returncode == 0 and "TEST SUCCEEDED" in output

        return success, output, recording_path
    except subprocess.TimeoutExpired:
        if recording_process:
            recording_process.kill()
        return False, "Test execution timed out after 5 minutes", recording_path
    except Exception as e:
        if recording_process:
            recording_process.kill()
        return False, f"Failed to run test: {str(e)}", recording_path

def extract_test_summary(output: str) -> dict:
    """Extract test results summary from xcodebuild output"""
    summary = {
        "passed": False,
        "duration": "N/A",
        "assertions": 0,
        "errors": [],
        "failure_reason": None,
        "expected": None,
        "actual": None,
        "failed_element": None,
        "last_successful_step": None
    }

    # Check if test succeeded
    if "TEST SUCCEEDED" in output:
        summary["passed"] = True
    elif "TEST FAILED" in output:
        summary["passed"] = False

    # Extract duration
    duration_match = re.search(r'Test Case.*finished in ([\d.]+) seconds', output)
    if duration_match:
        summary["duration"] = f"{duration_match.group(1)}s"

    # Count assertions
    assertions = len(re.findall(r'XCTAssert', output))
    summary["assertions"] = assertions

    # Extract error messages
    error_pattern = re.compile(r'error:.*?(?=\n\n|\Z)', re.DOTALL)
    errors = error_pattern.findall(output)
    summary["errors"] = errors[:5]  # Limit to 5 errors

    # Try to extract specific failure details
    if not summary["passed"]:
        # Look for XCTAssertTrue/False failures with element info
        # Pattern: XCTAssertTrue failed - "Element should exist"
        assert_true_fail = re.search(r'XCTAssertTrue failed[:\s-]*["\']?(.+?)["\']?\s*$', output, re.MULTILINE)
        if assert_true_fail:
            summary["expected"] = assert_true_fail.group(1).strip()
            summary["actual"] = "The condition was false"

        # Look for element existence failures
        # Pattern: "emailTextField" exists is false
        element_exists_fail = re.search(r'["\'](\w+)["\'].*?exists.*?(true|false)', output, re.IGNORECASE)
        if element_exists_fail:
            element_name = element_exists_fail.group(1)
            summary["failed_element"] = element_name
            summary["expected"] = f"UI element '{element_name}' should be visible on screen"
            summary["actual"] = f"Element '{element_name}' was not found or not visible"

        # Look for waitForExistence timeout
        wait_timeout = re.search(r'waitForExistence.*?(\w+(?:TextField|Button|Tab|View|Label|Cell))', output, re.IGNORECASE)
        if wait_timeout:
            element_name = wait_timeout.group(1)
            summary["failed_element"] = element_name
            summary["expected"] = f"Element '{element_name}' should appear within timeout"
            summary["actual"] = f"Element '{element_name}' did not appear in time"

        # Look for specific assertion messages
        # Pattern: XCTAssert failed: "Expected X but got Y"
        assertion_message = re.search(r'XCTAssert\w+.*?failed.*?["\'](.+?)["\']', output)
        if assertion_message and not summary["expected"]:
            msg = assertion_message.group(1)
            summary["failure_reason"] = msg
            # Try to parse expected/actual from message
            if "should" in msg.lower():
                summary["expected"] = msg
                summary["actual"] = "The expected condition was not met"

        # Look for error message verification failures
        error_msg_fail = re.search(r'(error.*?message|alert|toast).*?(not found|not exist|not visible)', output, re.IGNORECASE)
        if error_msg_fail:
            summary["expected"] = "An error message should be displayed"
            summary["actual"] = "No error message was found on screen"

        # Look for navigation failures
        nav_fail = re.search(r'(Items|Profile|Login|Detail).*?(Tab|View|Screen).*?(not found|not exist|not visible)', output, re.IGNORECASE)
        if nav_fail:
            screen_name = f"{nav_fail.group(1)} {nav_fail.group(2)}"
            summary["expected"] = f"Should navigate to {screen_name}"
            summary["actual"] = f"{screen_name} was not displayed"

        # Extract last successful action for context
        successful_taps = re.findall(r'tap\(\).*?(\w+(?:Button|Tab|Field|Cell))', output)
        if successful_taps:
            summary["last_successful_step"] = f"Last action: tapped '{successful_taps[-1]}'"

        # Fallback failure reason
        if not summary["failure_reason"] and not summary["expected"]:
            if "not exist" in output.lower() or "not found" in output.lower():
                summary["failure_reason"] = "A required UI element was not found"
            elif "timed out" in output.lower():
                summary["failure_reason"] = "Test timed out waiting for an element"
            else:
                summary["failure_reason"] = "Test assertion failed"

    return summary

def generate_human_summary(description: str, summary: dict, output: str) -> str:
    """Generate a human-readable summary of what happened during the test"""

    lines = []

    if summary["passed"]:
        lines.append("### Test Completed Successfully")
        lines.append("")
        lines.append(f"**What was tested:** {description}")
        lines.append("")
        lines.append("**What happened:**")

        # Parse the test steps from output
        steps = extract_test_steps(output)
        if steps:
            for step in steps:
                lines.append(f"- {step}")
        else:
            lines.append("- The app launched successfully")
            lines.append("- All UI interactions completed as expected")
            lines.append("- All verifications passed")

        lines.append("")
        lines.append(f"**Duration:** {summary['duration']}")

    else:
        lines.append("### Test Failed")
        lines.append("")
        lines.append(f"**What was tested:** {description}")
        lines.append("")

        # Show Expected vs Actual
        if summary.get("expected") or summary.get("actual"):
            lines.append("---")
            lines.append("")
            if summary.get("expected"):
                lines.append(f"**Expected:** {summary['expected']}")
            if summary.get("actual"):
                lines.append(f"**Actual:** {summary['actual']}")
            lines.append("")
            lines.append("---")
        elif summary.get("failure_reason"):
            lines.append(f"**Why it failed:** {summary['failure_reason']}")

        # Show failed element if identified
        if summary.get("failed_element"):
            lines.append("")
            lines.append(f"**Failed at element:** `{summary['failed_element']}`")

        # Show last successful step for context
        if summary.get("last_successful_step"):
            lines.append(f"**{summary['last_successful_step']}**")

        lines.append("")
        lines.append("**Possible causes:**")

        # Analyze the failure and provide helpful suggestions
        if summary.get("failed_element"):
            element = summary["failed_element"]
            lines.append(f"- The element `{element}` may not exist in the current screen")
            lines.append(f"- The accessibility identifier might be different")
            lines.append("- The screen might not have fully loaded")
        elif "not exist" in output.lower() or "not found" in output.lower():
            lines.append("- A UI element was not found on screen")
            lines.append("- The element might have a different accessibility identifier")
            lines.append("- The screen might not have loaded in time")
        elif "timed out" in output.lower():
            lines.append("- The app took too long to respond")
            lines.append("- A screen transition didn't complete in time")
            lines.append("- Network requests might be slow")
        elif "failed" in output.lower() and "assert" in output.lower():
            lines.append("- An expected condition was not met")
            lines.append("- The app behavior didn't match expectations")
        else:
            lines.append("- Check the detailed error log below for more information")

        lines.append("")
        lines.append(f"**Duration:** {summary['duration']}")

    return "\n".join(lines)

def extract_test_steps(output: str) -> list:
    """Extract readable test steps from the output"""
    steps = []

    # Look for common patterns in test execution
    if "app.launch()" in output or "launched" in output.lower():
        steps.append("App launched successfully")

    # Look for text field interactions
    text_fields = re.findall(r'(\w+TextField).*?typeText\("([^"]+)"\)', output)
    for field, text in text_fields:
        field_name = field.replace("TextField", "").lower()
        if "password" in field_name.lower():
            steps.append(f"Entered password in {field_name} field")
        elif "email" in field_name.lower():
            steps.append(f"Entered '{text}' in {field_name} field")
        else:
            steps.append(f"Entered text in {field_name} field")

    # Look for button taps
    button_taps = re.findall(r'(\w+Button).*?tap\(\)', output)
    for button in button_taps:
        button_name = button.replace("Button", "").lower()
        steps.append(f"Tapped the {button_name} button")

    # Look for successful assertions
    if "TEST SUCCEEDED" in output:
        steps.append("All verifications passed")

    return steps

# Page config
st.set_page_config(
    page_title="iOS Test Automator",
    page_icon="📱",
    layout="wide"
)

# Header
st.title("📱 iOS Test Automator")
st.markdown("Generate and run iOS UI tests using natural language descriptions")

# Sidebar
with st.sidebar:
    st.header("Configuration")

    st.subheader("Backend Status")
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=2)
        if response.status_code == 200:
            st.success("✅ Backend Connected")
        else:
            st.error("❌ Backend Error")
    except:
        st.error("❌ Backend Offline")
        st.info(f"Start backend with:\n```bash\ncd python-backend\nsource venv/bin/activate\npython main.py\n```")

    st.subheader("Simulator")
    simulator_id = get_simulator_id(SIMULATOR_NAME)
    if simulator_id:
        st.success(f"📱 {SIMULATOR_NAME}")
        st.caption(f"ID: {simulator_id[:8]}...")
    else:
        st.error(f"❌ {SIMULATOR_NAME} not found")

    st.subheader("Project")
    st.text(f"📂 {XCODE_PROJECT.split('/')[-1]}")
    st.text(f"🎯 {XCODE_SCHEME}")

    st.divider()

    if st.button("🔄 Clear History"):
        st.session_state.test_history = []
        save_history([])
        st.rerun()

# Main content
tab1, tab2 = st.tabs(["🚀 New Test", "📊 Test History"])

with tab1:
    st.header("Create New Test")

    # Test description input
    test_description = st.text_area(
        "Describe the test you want to run",
        placeholder="Example: Test login with invalid credentials and verify error message appears",
        height=100,
        help="Describe what you want to test in natural language"
    )

    # Optional: Custom class name
    with st.expander("Advanced Options"):
        custom_class_name = st.text_input(
            "Custom Class Name (optional)",
            placeholder="Leave empty to auto-generate",
            help="Provide a custom Swift class name for the test"
        )
        force_clean_build = st.checkbox(
            "Force Clean Build",
            value=False,
            help="Enable to do a full clean build. Leave unchecked for faster incremental builds."
        )

    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        generate_btn = st.button("🔨 Generate Test", type="primary", use_container_width=True)

    with col2:
        run_btn = st.button("▶️ Generate & Run", type="secondary", use_container_width=True)

    # Generate test
    if generate_btn or run_btn:
        if not test_description.strip():
            st.error("Please enter a test description")
        else:
            # Generate class name
            class_name = custom_class_name.strip() if custom_class_name.strip() else sanitize_class_name(test_description)

            with st.spinner("🤖 Generating test code with RAG..."):
                test_data = generate_test(test_description, class_name)

            if test_data:
                st.success("✅ Test generated successfully!")

                # Display generated code
                st.subheader("Generated Test Code")
                with st.expander("View Swift Code", expanded=True):
                    st.code(test_data["swift_code"], language="swift")

                # Display RAG context
                rag_context = test_data["metadata"].get("rag_context", {})
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Accessibility IDs Found", rag_context.get("accessibility_ids_found", 0))
                with col2:
                    st.metric("Screens Found", rag_context.get("screens_found", 0))
                with col3:
                    st.metric("Docs Retrieved", rag_context.get("total_docs_retrieved", 0))

                # Save test file
                with st.spinner("💾 Saving test file..."):
                    file_path = save_test_file(test_data["swift_code"], class_name)

                if file_path:
                    st.info(f"📁 Test saved to: `{file_path}`")
                    st.session_state.current_test = {
                        "class_name": class_name,
                        "description": test_description,
                        "code": test_data["swift_code"],
                        "file_path": file_path,
                        "timestamp": datetime.now()
                    }

                    # Auto-run if requested
                    if run_btn:
                        st.divider()
                        st.subheader("🏃 Running Test")

                        # Get simulator ID
                        sim_id = get_simulator_id(SIMULATOR_NAME)
                        if not sim_id:
                            st.error(f"Cannot find simulator: {SIMULATOR_NAME}")
                        else:
                            st.info(f"📱 Using Simulator: {SIMULATOR_NAME} (ID: {sim_id})")
                            progress_bar = st.progress(0, text="[0/4] Preparing simulator...")

                            # Boot simulator
                            with st.spinner(f"Booting {SIMULATOR_NAME}..."):
                                if not boot_simulator(sim_id):
                                    st.error("Failed to boot simulator")
                                else:
                                    st.success(f"✅ Simulator booted: {SIMULATOR_NAME} ({sim_id[:8]}...)")
                                    progress_bar.progress(25, text="[1/4] Building project...")

                                    # Build (incremental by default, clean if requested)
                                    build_type = "clean build" if force_clean_build else "incremental build"
                                    with st.spinner(f"Building project ({build_type})..."):
                                        build_success, build_output = build_for_testing(sim_id, clean_build=force_clean_build)

                                    if not build_success:
                                        st.error("❌ Build failed")
                                        with st.expander("View Build Output"):
                                            st.text(build_output)
                                    else:
                                        st.success("✅ Build successful")
                                        progress_bar.progress(50, text="[2/4] Running test with video recording...")

                                        # Extract actual class name from generated code
                                        actual_class_name = extract_class_name_from_code(test_data["swift_code"])
                                        if not actual_class_name:
                                            st.error("Could not extract class name from generated code")
                                            actual_class_name = class_name  # fallback

                                        # Run test with recording
                                        with st.spinner(f"Running test on {SIMULATOR_NAME}... 📹 Recording video"):
                                            success, output, recording_path = run_xcode_test(
                                                actual_class_name,  # Use actual class name from code!
                                                test_data["swift_code"],
                                                sim_id,
                                                record_video=True
                                            )

                                        progress_bar.progress(100, text="[4/4] Test completed!")

                                        # Display results
                                        st.divider()
                                        st.subheader("📋 Test Results")

                                        summary = extract_test_summary(output)

                                        if success:
                                            st.success("✅ TEST PASSED")
                                        else:
                                            st.error("❌ TEST FAILED")

                                        # Metrics
                                        col1, col2, col3 = st.columns(3)
                                        with col1:
                                            st.metric("Duration", summary["duration"])
                                        with col2:
                                            st.metric("Status", "PASSED" if success else "FAILED")
                                        with col3:
                                            if recording_path and os.path.exists(recording_path):
                                                st.metric("Recording", "✅ Available")
                                            else:
                                                st.metric("Recording", "❌ Not Available")

                                        # Video recording
                                        if recording_path and os.path.exists(recording_path):
                                            st.divider()
                                            st.subheader("🎬 Test Recording")

                                            col1, col2 = st.columns([3, 1])
                                            with col1:
                                                st.video(recording_path)
                                            with col2:
                                                with open(recording_path, 'rb') as f:
                                                    st.download_button(
                                                        label="⬇️ Download Video",
                                                        data=f.read(),
                                                        file_name=os.path.basename(recording_path),
                                                        mime="video/mp4",
                                                        use_container_width=True
                                                    )
                                                st.caption(f"📁 {os.path.basename(recording_path)}")

                                        # Human-readable summary
                                        st.divider()
                                        human_summary = generate_human_summary(test_description, summary, output)
                                        st.markdown(human_summary)

                                        # Errors (detailed)
                                        if summary["errors"]:
                                            with st.expander("View Detailed Errors"):
                                                for error in summary["errors"]:
                                                    st.error(error)

                                        # Full output
                                        with st.expander("View Full Test Output"):
                                            st.text(output)

                                        # Add to history and persist to disk
                                        new_entry = {
                                            "class_name": class_name,
                                            "description": test_description,
                                            "passed": success,
                                            "duration": summary["duration"],
                                            "timestamp": datetime.now(),
                                            "output": output,
                                            "recording": recording_path if recording_path and os.path.exists(recording_path) else None,
                                            "human_summary": human_summary,
                                        }
                                        st.session_state.test_history.insert(0, new_entry)
                                        save_history(st.session_state.test_history)

with tab2:
    st.header("Test History")

    if not st.session_state.test_history:
        st.info("No tests run yet. Create and run a test to see history.")
    else:
        for idx, test in enumerate(st.session_state.test_history):
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

                with col1:
                    st.markdown(f"**{test['class_name']}**")
                    st.caption(test['description'][:100] + "..." if len(test['description']) > 100 else test['description'])

                with col2:
                    if test['passed']:
                        st.success("✅ PASSED")
                    else:
                        st.error("❌ FAILED")

                with col3:
                    st.text(test['duration'])

                with col4:
                    st.caption(test['timestamp'].strftime("%H:%M:%S"))

                with st.expander("View Details"):
                    # Human-readable summary
                    if test.get('human_summary'):
                        st.markdown(test['human_summary'])
                        st.divider()

                    # Video recording if available
                    if test.get('recording') and os.path.exists(test['recording']):
                        st.subheader("🎬 Test Recording")
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.video(test['recording'])
                        with col2:
                            with open(test['recording'], 'rb') as f:
                                st.download_button(
                                    label="⬇️ Download",
                                    data=f.read(),
                                    file_name=os.path.basename(test['recording']),
                                    mime="video/mp4",
                                    key=f"download_{idx}",
                                    use_container_width=True
                                )
                        st.divider()

                    # Test output (collapsed by default)
                    with st.expander("View Raw Test Output"):
                        st.text_area("Test Output", test['output'], height=200, key=f"output_{idx}")

                st.divider()

# Footer
st.divider()
st.caption("iOS Test Automator | Powered by Claude Sonnet 4.5 & RAG")
