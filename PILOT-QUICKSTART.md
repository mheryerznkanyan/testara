# 🚀 Testara Pilot — Quick Start

**Welcome to the Testara pilot program!**

This guide will get you up and running in 10 minutes.

---

## ✅ Prerequisites

Before you start, make sure you have:

- [ ] **Docker Desktop** installed ([download here](https://www.docker.com/products/docker-desktop))
- [ ] **Anthropic API key** ([get one here](https://console.anthropic.com/))
- [ ] **Your iOS app source code** (SwiftUI or UIKit project)

---

## 📥 Installation (10 Minutes)

### Step 1: Download Testara

```bash
# Clone the repository
git clone https://github.com/mheryerznkanyan/ios-test-automator-v2.git
cd ios-test-automator-v2
git checkout v2.0.0-pilot
```

---

### Step 2: Configure

Create a `.env` file with your settings:

```bash
cat > .env << EOF
ANTHROPIC_API_KEY=your_anthropic_key_here
IOS_APP_PATH=/path/to/your/ios/app
EOF
```

**Replace:**
- `your_anthropic_key_here` → your actual Anthropic API key
- `/path/to/your/ios/app` → path to your iOS project folder

---

### Step 3: Index Your iOS App (One-Time Setup)

This step analyzes your Swift code and builds a searchable index.

```bash
docker run --rm \
  -v $(pwd)/rag_store:/app/rag_store \
  -v /path/to/your/ios/app:/app/ios-app:ro \
  $(docker build -q -f Dockerfile.backend .) \
  python -m rag.cli ingest \
    --app-dir /app/ios-app \
    --persist /app/rag_store \
    --collection ios_app
```

**This will take 1-3 minutes** depending on your project size.

You'll see output like:
```json
{
  "status": "ok",
  "indexed_swift_files": 42,
  "documents_upserted": 156,
  "persist_dir": "/app/rag_store",
  "collection": "ios_app"
}
```

---

### Step 4: Start Testara

```bash
docker-compose up
```

**Wait for:**
```
backend_1  | INFO:     Application startup complete.
ui_1       | You can now view your Streamlit app in your browser.
ui_1       |   Local URL: http://localhost:8501
```

---

### Step 5: Open Testara

**Open in your browser:** http://localhost:8501

You should see the Testara UI! 🎉

---

## 🧪 Generate Your First Test

### In the Testara UI:

1. **Describe your test** (in plain English):
   ```
   test login with valid credentials
   ```

2. Click **🔨 Generate Test**

3. **Watch Testara:**
   - Enrich your description
   - Search your Swift code for relevant context
   - Generate a complete XCUITest

4. **Copy the generated Swift code** and paste it into your Xcode project

5. **Run the test** in Xcode (⌘U)

---

## ❓ Troubleshooting

### "Backend not reachable"
```bash
# Check if backend is running
docker-compose ps

# Restart if needed
docker-compose restart backend
```

### "RAG store is empty"
You skipped Step 3. Run the indexing command above.

### "Invalid API key"
Check your `.env` file — make sure `ANTHROPIC_API_KEY` is correct.

### Docker not working
- Make sure Docker Desktop is running
- Try: `docker ps` to verify Docker is active

---

## 💬 Get Help

**Having issues?**
- Open an issue: https://github.com/mheryerznkanyan/ios-test-automator-v2/issues
- Email: mher@testara.dev
- Slack: [invite link from your onboarding email]

---

## 🎯 What to Test During Pilot

Try generating tests for:
- ✅ Login flows
- ✅ Tab navigation
- ✅ List interactions (scrolling, tapping items)
- ✅ Search functionality
- ✅ Form validation
- ✅ Error states

**Give us feedback on:**
- What works well?
- What doesn't work?
- What features are missing?
- How can we improve the UI?

---

## 📊 Pilot Program Details

**Duration:** 3 months  
**Cost:** Free  
**What you get:**
- Unlimited test generation
- Direct access to the founder (Mher)
- Priority feature requests
- Your feedback shapes the product

**What we need from you:**
- Use Testara for real work
- Share feedback (weekly check-ins)
- Report bugs when you find them
- Be willing to do a testimonial if you like it

---

## 🚀 Next Steps

1. **Generate 5-10 tests** for your app
2. **Run them in Xcode** and see how they perform
3. **Share feedback** (what worked, what didn't)
4. **Weekly sync call** with Mher to discuss improvements

---

**Welcome aboard! Let's build something great together.** 🎉

— Mher & the Testara team
