# Testara

**AI-powered iOS test automation** — Write tests in plain English, get working XCTest code.

---

## 🚀 Quick Start

### Prerequisites

- **macOS** with Xcode installed (required for iOS simulators)
- **Python 3.11+**
- **Node.js 20+**
- Anthropic API key ([get one](https://console.anthropic.com/))
- Your iOS app source code

### 1. Configure

```bash
git clone https://github.com/mheryerznkanyan/testara.git
cd testara

cp .env.example .env
# Edit .env:
#   - Set ANTHROPIC_API_KEY to your API key
#   - Set PROJECT_ROOT to the absolute path of your iOS project
```

### 2. Start

```bash
./start.sh
```

**Features:**
- 🎨 Colorful ASCII art banner
- ✅ Visual status indicators
- 📊 Formatted tables for config and services
- 🌈 Rich terminal experience

### 3. Open in browser

- **Frontend:** http://localhost:3000
- **API:** http://localhost:8000

---

## ⚙️ Configuration

**Edit `.env`:**

```bash
# Required
ANTHROPIC_API_KEY=your_key_here

# Your iOS app
PROJECT_ROOT=/path/to/your/ios/app
XCODE_PROJECT=/path/to/YourApp.xcodeproj
XCODE_UI_TEST_TARGET=YourAppUITests
```

**First-time setup:** `./start.sh` automatically:
- Creates `LLMGeneratedTest.swift` in your UI test target
- Adds it to your Xcode project (using `pbxproj`)
- Generated tests will be written to this file

**If auto-setup fails,** manually add the file:
1. Create `YourAppUITests/LLMGeneratedTest.swift` (empty file)
2. In Xcode: Right-click test target → Add Files → Select the file
3. Make sure your UI test target is checked

---

## 🎯 Usage

Your iOS app is automatically indexed on first run. To re-index after code changes:

```bash
python -m rag.cli ingest --app-dir "$PROJECT_ROOT" --persist ./rag_store
```

### Generate Tests

**Via Frontend UI:**
- Open http://localhost:3000
- Enter: "Test login with valid credentials"
- Click "Generate"
- Copy the XCTest code

**Via API:**
```bash
curl -X POST http://localhost:8000/generate-test-with-rag \
  -H "Content-Type: application/json" \
  -d '{"description": "Test login with valid credentials"}'
```

### Run in Xcode

Copy generated code → paste into your XCUITest target → run!

---

## 🏗️ Architecture

```
Next.js Frontend (port 3000)
         ↓
  FastAPI Backend (port 8000)
         ↓
    RAG + Claude AI
         ↓
   Generated XCTest Code
```

---

## 📚 Documentation

- **[Setup Guide](DEPLOYMENT.md)** — Advanced setup options
- **[Contributing](CONTRIBUTING.md)** — How to contribute

---

## 🐛 Troubleshooting

**Backend won't start?**
```bash
# Check Python dependencies
pip install -e .
```

**Can't connect to frontend?**
```bash
# Make sure both services are running
# Backend: uvicorn app.main:app --port 8000
# Frontend: npm run dev (in frontend/)
```

---

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 📄 License

MIT License — see [LICENSE](LICENSE)

---

## 🔗 Links

- **GitHub:** https://github.com/mheryerznkanyan/testara
- **Issues:** https://github.com/mheryerznkanyan/testara/issues

---

Made with ⚡ by [Mher Yerznkanyan](https://github.com/mheryerznkanyan)
