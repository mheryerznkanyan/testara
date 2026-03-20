# Appium Discovery Integration — Implementation Plan

## Problem
Static Swift source analysis (RAG + AST) cannot reliably resolve accessibility identifiers
because labels come from localization chains, computed properties, and multi-file indirection.
The LLM guesses wrong identifiers → tests fail.

## Solution
Before test generation, run a **live discovery phase** using Appium/WebDriverAgent:
1. Launch the app in the simulator (already booted by test_runner)
2. Get `driver.page_source` — live XML accessibility tree with REAL runtime values
3. Parse XML → structured element list (name=actual identifier, label=visible text)
4. Feed this into the LLM as ground truth alongside existing RAG context

The XML `name` attribute IS the `.accessibilityIdentifier` — fully resolved at runtime.
The XML `label` attribute IS the visible text — localization fully resolved.
No more guessing.

## Architecture

```
BEFORE (current):
  description → RAG (static Swift) → LLM → XCUITest code

AFTER (new):
  description
    + AccessibilitySnapshot (live XML tree from running app)  ← NEW
    + RAG context (static, kept as fallback)
    → LLM → XCUITest code (using REAL identifiers)
```

## New Files

### `backend/app/services/appium_discovery_service.py`
```
AppiumDiscoveryService
  - start_appium_server()       # subprocess: appium --port 4723
  - is_server_running() → bool
  - discover(bundle_id, device_udid, screen_hints?) → AccessibilitySnapshot
  - _parse_wda_xml(xml) → list[ElementInfo]
  - stop()

AccessibilitySnapshot
  - elements: list[ElementInfo]
  - screenshot_b64: str
  - raw_xml: str
  - captured_at: datetime
  - to_context_string() → str   # LLM-ready format

ElementInfo (dataclass)
  - element_type: str           # XCUIElementTypeButton etc.
  - name: str                   # = .accessibilityIdentifier (THE KEY)
  - label: str                  # = visible text (localization resolved)
  - value: str                  # = current content
  - enabled: bool
  - visible: bool
  - x, y, width, height: int
  - is_interactive: bool        # Button, TextField, SecureTextField, Toggle, TabBar item
```

### `backend/app/utils/accessibility_tree_parser.py`
```
parse_wda_xml(xml_string) → list[ElementInfo]
filter_interactive(elements) → list[ElementInfo]
elements_to_context_string(elements) → str
```

### `docs/APPIUM_SETUP.md`
Full setup guide: install Node.js, install appium, install xcuitest driver,
configure .env, troubleshoot common issues.

## Modified Files

### `backend/app/core/config.py`
```python
appium_enabled: bool = False
appium_server_url: str = "http://localhost:4723"
appium_startup_timeout: int = 30
appium_discovery_timeout: int = 60
```

### `backend/app/schemas/test_schemas.py`
```python
# Add to RAGTestGenerationRequest:
discovery_enabled: bool = False   # trigger live Appium discovery
bundle_id: Optional[str] = None   # e.g. "com.example.MyApp"
device_udid: Optional[str] = None # use booted simulator UDID
```

### `backend/app/services/test_generator.py`
```python
# Add optional param to run():
def run(self, request, accessibility_snapshot=None) → TestGenerationResponse

# When snapshot provided, inject runtime tree into user_message:
runtime_section = snapshot.to_context_string()
# Prepend to context section — LLM uses real IDs first
```

### `backend/app/core/prompts.py`
Add RUNTIME_TREE_SECTION that explains:
- Runtime tree is from live running app — highest confidence
- name = actual .accessibilityIdentifier
- label = resolved visible text
- Use name for element queries: app.buttons["name_value"]
- Priority: runtime tree > explicit RAG IDs > inferred IDs > label fallback

### `backend/app/api/routes/` — new file `discovery.py`
```
POST /discover
  body: { bundle_id, device_udid, screen_hints? }
  response: { elements: [...], screenshot_url, snapshot_id }
  
Stores snapshot in app.state, returns snapshot_id.
Test generation requests can reference snapshot_id.
```

### `backend/app/main.py`
- Import and init AppiumDiscoveryService in lifespan (if appium_enabled)
- Register /discover router

### `pyproject.toml`
```
Appium-Python-Client >= 4.0.0
```

## Key Implementation Details

### Appium server management
- Check if already running: `GET http://localhost:4723/status`
- If not, spawn: `subprocess.Popen(['appium', '--port', '4723', '--log-level', 'error'])`
- Wait up to 30s for it to respond
- Don't kill it on teardown (user may want it persistent)

### WDA XML parsing
The XML has this structure:
```xml
<XCUIElementTypeApplication name="AppName" label="AppName">
  <XCUIElementTypeWindow>
    <XCUIElementTypeButton name="loginButton" label="Sign In" 
      enabled="true" visible="true" x="20" y="400" width="350" height="44"/>
    <XCUIElementTypeTextField name="emailField" label="Email" 
      value="placeholder: Enter email" .../>
  </XCUIElementTypeWindow>
</XCUIElementTypeApplication>
```
Parse with `xml.etree.ElementTree`. Filter to interactive types.
Skip elements where `name` is empty or equals the element type name.

### Appium capabilities for iOS simulator
```python
from appium.options import XCUITestOptions

opts = XCUITestOptions()
opts.platform_name = "iOS"
opts.bundle_id = bundle_id
opts.udid = device_udid       # UDID of already-booted simulator
opts.no_reset = True          # don't reinstall/clear app data
opts.automation_name = "XCUITest"
opts.should_use_singleton_test_manager = False
opts.new_command_timeout = 60
```

### LLM context format
```
RUNTIME ACCESSIBILITY TREE (captured from live app — highest confidence):
Source: Appium/WebDriverAgent live snapshot
Note: 'name' = .accessibilityIdentifier, 'label' = resolved visible text

Interactive elements found:
  [Button]        name="loginButton"       label="Sign In"          frame=(20,400,350,44)
  [Button]        name="signupButton"      label="Create Account"   frame=(20,460,350,44)
  [TextField]     name="emailTextField"    label="Email"            value="placeholder: Enter email"
  [SecureField]   name="passwordTextField" label="Password"
  [StaticText]    name="errorLabel"        label=""                 (currently empty)

RULE: Use name values directly in XCUITest queries:
  app.buttons["loginButton"]         ✅ CORRECT (name from runtime tree)
  app.buttons["Sign In"]             ⚠️  FALLBACK ONLY (label, may break on localization)
```

## Fallback Strategy
If Appium not enabled/available:
- Gracefully degrade to current RAG-only approach
- Log warning: "Appium discovery disabled, using static analysis only"
- No hard dependency — Appium is optional

## Testing
- Unit test: parse_wda_xml() with sample XML fixture
- Integration test: requires Appium + simulator (skip in CI unless APPIUM_ENABLED=true)
- Manual test: run against HackerNews iOS app, verify element names match source code

## Setup Requirements (user-facing)
```bash
# Install Node.js (if not present)
brew install node

# Install Appium
npm install -g appium

# Install XCUITest driver
appium driver install xcuitest

# Verify
appium driver list --installed

# Start (or let Testara auto-start)
appium --port 4723

# In .env:
APPIUM_ENABLED=true
APPIUM_SERVER_URL=http://localhost:4723
```
