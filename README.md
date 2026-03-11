# Testara

**AI-powered iOS test automation** — Write tests in plain English, get working XCTest code.

---

## 🚀 Quick Start

```bash
git clone https://github.com/mheryerznkanyan/testara.git
cd testara

# 1. Configure
cp .env.example .env
# Edit .env: add your ANTHROPIC_API_KEY

# 2. Start everything with Docker
docker-compose up -d

# 3. Open in browser
# Frontend: http://localhost:3000
# API: http://localhost:8000
```

**That's it!** ✨

---

## 📋 What You Need

- Docker Desktop ([download](https://www.docker.com/products/docker-desktop))
- Anthropic API key ([get one](https://console.anthropic.com/))
- Your iOS app source code

---

## ⚙️ Configuration

**Edit `.env`:**

```bash
# Required
ANTHROPIC_API_KEY=your_key_here

# Your iOS app (for indexing)
PROJECT_ROOT=/path/to/your/ios/app
XCODE_PROJECT=/path/to/YourApp.xcodeproj
XCODE_SCHEME=YourApp
```

---

## 🎯 Usage

### 1. Index Your iOS App

```bash
docker-compose exec backend python -m rag.cli ingest \
  --app-dir /app/ios-app \
  --persist /app/rag_store

docker-compose exec backend python generate_app_context.py
```

### 2. Generate Tests

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

### 3. Add to Xcode

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

**All running in Docker containers.**

---

## 📚 Documentation

- **[Setup Guide](DEPLOYMENT.md)** — Advanced setup options
- **[Settings](SETTINGS-GUIDE.md)** — Configuration details
- **[Contributing](CONTRIBUTING.md)** — How to contribute

---

## 🐛 Troubleshooting

**Backend won't start?**
```bash
docker-compose logs backend
```

**Can't connect to frontend?**
```bash
docker-compose ps  # Check if containers are running
```

**Restart everything:**
```bash
docker-compose restart
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
