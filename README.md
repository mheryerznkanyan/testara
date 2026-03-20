# [Testara](https://testara.dev)

**AI-powered iOS test automation** — Describe tests in plain English, get working XCUITest code that runs on your simulator.

**Website:** [testara.dev](https://testara.dev)

---

## How It Works

```
Describe test in plain English
         ↓
  Appium discovers your app's UI (live accessibility tree)
         ↓
  RAG retrieves relevant source code context
         ↓
  Claude generates XCUITest Swift code
         ↓
  Test runs on iOS Simulator with video recording
```

---

## Quick Start

### Prerequisites

- **macOS** with Xcode installed
- **Python 3.11+**
- **Node.js 20+**
- **Appium** (optional, for live UI discovery)
- Anthropic API key ([get one](https://console.anthropic.com/))

### 1. Configure

```bash
git clone https://github.com/mheryerznkanyan/testara.git
cd testara
cp .env.example .env
```

Edit `.env`:
```bash
# Required
ANTHROPIC_API_KEY=your_key_here
PROJECT_ROOT=/path/to/your/ios/app

# Optional: login credentials (for apps that require authentication)
TEST_CREDENTIALS_EMAIL=test@example.com
TEST_CREDENTIALS_PASSWORD=password123

# Optional: disable heavy SDKs that cause main thread stalls
LAUNCH_ENVIRONMENT=DISABLE_ANALYTICS=1

# Optional: Xcode test plan
XCODE_TEST_PLAN=MyTestPlan
```

### 2. Start

```bash
./start.sh
```

First run automatically:
- Indexes your app's source code for RAG
- Creates `LLMGeneratedTest.swift` in your UI test target
- Adds it to your Xcode project

### 3. Use

Open http://localhost:3000 and describe your test:

> "Search for Classic item and click on the first result"

Testara will generate the test, run it on the simulator, and show you a video recording.

---

## Appium Discovery (Recommended)

Appium provides **live UI discovery** — it launches your app, navigates to the target screen, and captures the real accessibility tree. This gives the LLM accurate element identifiers instead of guessing.

### Setup

```bash
npm install -g appium
appium driver install xcuitest
```

Enable in `.env`:
```bash
APPIUM_ENABLED=true
```

Then configure your **Bundle ID** and **Device UDID** in the Settings page (http://localhost:3000/settings).

See [docs/APPIUM_SETUP.md](docs/APPIUM_SETUP.md) for details.

---

## Configuration Reference

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | Your Anthropic API key |
| `PROJECT_ROOT` | Yes | Absolute path to your iOS project |
| `TEST_CREDENTIALS_EMAIL` | No | Email for apps requiring login |
| `TEST_CREDENTIALS_PASSWORD` | No | Password for apps requiring login |
| `LAUNCH_ENVIRONMENT` | No | Comma-separated `KEY=VALUE` pairs passed to app's `launchEnvironment` |
| `XCODE_TEST_PLAN` | No | Xcode test plan name (if your project uses one) |
| `APPIUM_ENABLED` | No | Enable Appium live UI discovery (`true`/`false`) |
| `APPIUM_SERVER_URL` | No | Appium server URL (default: `http://localhost:4723`) |

### Switching Projects

When you change `PROJECT_ROOT`, Testara auto-detects the change and re-indexes. To force a full re-index:

```bash
./start.sh --reindex
```

---

## Architecture

```
Next.js Frontend (port 3000)
         ↓
  FastAPI Backend (port 8000)
    ├── Description Enrichment (Claude)
    ├── RAG Context (ChromaDB + source code)
    ├── Appium Discovery (live accessibility tree)
    └── Test Generation (Claude)
         ↓
  xcodebuild (test execution + video recording)
```

### Key Components

- **Navigation Service** — Static analysis of SwiftUI/UIKit navigation patterns, detects login requirements
- **Appium Discovery** — Launches app via WDA, navigates to target screen, captures real accessibility identifiers
- **Test Generator** — Combines runtime tree + RAG context + navigation context into an LLM prompt
- **Test Runner** — Writes test to Xcode project, builds, runs via `xcodebuild`, records video

---

## Troubleshooting

**Tests hang at `app.launch()`?**
Your app likely has heavy SDKs (Sentry, Firebase) that cause main thread stalls. Add a launch environment variable that your app checks to skip SDK initialization during tests:
```bash
LAUNCH_ENVIRONMENT=DISABLE_ANALYTICS=1,RUNNING_TESTS=1
```

**Wrong accessibility IDs in generated tests?**
Make sure the RAG index is up to date. Run `./start.sh --reindex` after making changes to your app's source code.

**Appium can't connect?**
```bash
# Check Appium is running
appium --version
appium driver list --installed

# Start manually if needed
appium --port 4723
```

---

## Documentation

- **[Appium Setup Guide](docs/APPIUM_SETUP.md)** — Detailed Appium configuration
- **[Setup Guide](DEPLOYMENT.md)** — Advanced deployment options

---

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md)

---

## License

MIT License — see [LICENSE](LICENSE)

---

## Links

- **Website:** [testara.dev](https://testara.dev)
- **GitHub:** [github.com/mheryerznkanyan/testara](https://github.com/mheryerznkanyan/testara)
- **Issues:** [Report a bug](https://github.com/mheryerznkanyan/testara/issues)

---

Made with ⚡ by [Mher Yerznkanyan](https://github.com/mheryerznkanyan)
