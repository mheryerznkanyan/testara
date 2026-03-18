# Appium Setup Guide for Testara

Testara uses Appium to capture a **live accessibility tree** from a running iOS Simulator app. This gives the AI test generator the highest-confidence element identifiers directly from the running app — no static analysis required.

> **macOS only.** Appium's XCUITest driver requires Xcode and iOS Simulator, which are macOS-exclusive.

---

## Prerequisites

| Requirement | Notes |
|---|---|
| macOS 13+ | Ventura or newer recommended |
| Xcode 15+ | Install from the App Store |
| Xcode Command Line Tools | `xcode-select --install` |
| Node.js 18+ | Install via [nvm](https://github.com/nvm-sh/nvm) or `brew install node` |
| Python 3.11+ | Already required by Testara backend |

Verify Xcode is set up:

```bash
xcode-select -p          # Should print a path like /Applications/Xcode.app/...
xcrun simctl list        # Should list available simulators
```

---

## 1. Install Appium

```bash
npm install -g appium
```

Verify:

```bash
appium --version         # e.g. 2.5.x
```

---

## 2. Install the XCUITest Driver

```bash
appium driver install xcuitest
```

This downloads and builds WebDriverAgent (WDA), which is the bridge between Appium and iOS Simulator.

---

## 3. Verify Installation

```bash
appium driver list --installed
```

Expected output:
```
✓ xcuitest@x.x.x [installed (npm)]
```

---

## 4. Start the Appium Server

```bash
appium --port 4723
```

Leave this running in a terminal tab. Testara will connect to it automatically.

Alternatively, Testara can **auto-start Appium** if `appium` is in your `PATH` — see Configuration below.

---

## 5. Configure Testara

Add these to your `.env` file (or `backend/.env`):

```env
# Enable Appium-based live accessibility discovery
APPIUM_ENABLED=true

# URL of the running Appium server
APPIUM_SERVER_URL=http://localhost:4723
```

If `APPIUM_ENABLED` is `false` (default), Testara falls back to static analysis only.

---

## 6. How Discovery Works

When Testara generates tests for an iOS app:

1. **Simulator boot** — Testara boots the target simulator (same flow as `test_runner.py`).
2. **App launch via Appium** — `AppiumDiscoveryService` opens a WebDriver session, launching the app.
3. **Accessibility tree capture** — `driver.page_source` returns a live XML snapshot of every UI element with its `name` (accessibility identifier), `label` (visible text), and `value`.
4. **XML parsing** — `accessibility_tree_parser.py` walks the XML, filtering for interactive elements that have meaningful identifiers.
5. **Context injection** — The formatted tree is injected into the LLM prompt as `RUNTIME ACCESSIBILITY TREE`, giving the model ground-truth `name` values to use in XCUITest selectors like `app.buttons["submitButton"]`.
6. **Session cleanup** — The Appium session is closed; the simulator stays booted for subsequent test runs.

---

## 7. Common Issues

### WDA Build Fails

WebDriverAgent needs to be code-signed to run on Simulator. Usually this is automatic, but if it fails:

```bash
# Check Xcode developer account is set up
open -a Xcode
# Preferences → Accounts → Add Apple ID
```

Also try resetting WDA:
```bash
appium driver uninstall xcuitest
appium driver install xcuitest
```

### Simulator Not Booted

Appium requires the target simulator to already be **booted** before starting a session. Testara handles this automatically via `xcrun simctl boot <udid>`, but if you're running discovery manually, boot the simulator first:

```bash
xcrun simctl boot "iPhone 15 Pro"
open -a Simulator
```

### Bundle ID Not Found

If Appium can't find the app, the bundle ID may be wrong or the app isn't installed on the simulator:

```bash
# List installed apps on booted simulator
xcrun simctl listapps booted | grep -i <appname>
```

### Port 4723 Already in Use

```bash
lsof -i :4723            # Find what's using the port
kill -9 <PID>            # Kill it
appium --port 4723       # Restart
```

### `Appium-Python-Client` Not Installed

The Appium Python client is an optional dependency. Install it in the backend virtualenv:

```bash
cd backend
pip install Appium-Python-Client
```

---

## 8. Auto-Start Behavior

If `APPIUM_ENABLED=true` and Testara detects that the Appium server is not running, it will attempt to start it automatically by calling:

```bash
appium --port 4723 --log-level error
```

This requires `appium` to be in the system `PATH`. To check:

```bash
which appium     # Should print e.g. /usr/local/bin/appium
```

If Appium is not in PATH (e.g. installed in a non-standard location), start it manually before running Testara.
