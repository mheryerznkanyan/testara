# 📦 Testara Deployment Guide

**For Pilot Users**

---

## 🎯 Recommended: Docker (Easiest)

**Prerequisites:**
- Docker Desktop installed ([download](https://www.docker.com/products/docker-desktop))
- Your iOS app source code
- Anthropic API key

**Time:** 10 minutes

---

## Quick Start (Docker)

### 1. Clone the Repo
```bash
git clone https://github.com/mheryerznkanyan/ios-test-automator-v2.git
cd ios-test-automator-v2
git checkout v2.0.0-pilot
```

### 2. Configure
```bash
# Create .env file
cat > .env << EOF
ANTHROPIC_API_KEY=your_anthropic_key_here
IOS_APP_PATH=/path/to/your/ios/app
EOF
```

### 3. Index Your iOS App (One-Time)
```bash
# Run indexing container
docker run --rm \
  -v ./rag_store:/app/rag_store \
  -v /path/to/your/ios/app:/app/ios-app:ro \
  -e ANTHROPIC_API_KEY=your_key \
  testara-backend \
  python -m rag.cli ingest \
    --app-dir /app/ios-app \
    --persist /app/rag_store \
    --collection ios_app
```

### 4. Start Testara
```bash
docker-compose up
```

### 5. Open in Browser
- **UI:** http://localhost:8501
- **API:** http://localhost:8000/docs

---

## Alternative: Local Install (Advanced Users)

### Prerequisites
- Python 3.11+
- pip or uv

### Steps

```bash
# 1. Clone
git clone https://github.com/mheryerznkanyan/ios-test-automator-v2.git
cd ios-test-automator-v2
git checkout v2.0.0-pilot

# 2. Install
pip install -e .

# 3. Configure
cat > .env << EOF
ANTHROPIC_API_KEY=your_key
PROJECT_ROOT=/path/to/your/ios/app
EOF

# 4. Index your iOS app
python -m rag.cli ingest \
  --app-dir /path/to/your/ios/app \
  --persist ./rag_store \
  --collection ios_app

# 5. Start backend (Terminal 1)
cd backend
uvicorn app.main:app --reload

# 6. Start UI (Terminal 2)
streamlit run ui/app.py
```

---

## For Production / Team Use

### Option A: Deploy to Cloud (DigitalOcean, AWS, GCP)

**Recommended:** DigitalOcean App Platform (easiest)

1. Fork the repo to your GitHub
2. Connect to DigitalOcean App Platform
3. Set environment variables:
   - `ANTHROPIC_API_KEY`
   - `PROJECT_ROOT` (mount iOS app as volume)
4. Deploy

**Cost:** ~$12/mo (basic tier)

---

### Option B: Self-Hosted on Company Server

**Requirements:**
- Linux server with Docker
- Port 8000 (backend) and 8501 (UI) open

**Setup:**
```bash
# On server
git clone https://github.com/mheryerznkanyan/ios-test-automator-v2.git
cd ios-test-automator-v2

# Configure
echo "ANTHROPIC_API_KEY=your_key" > .env
echo "IOS_APP_PATH=/path/to/ios/app" >> .env

# Run
docker-compose up -d

# Access via http://server-ip:8501
```

---

## Distributing to Pilot Users

### Method 1: GitHub Release (Recommended for Pilot)

**What users do:**
1. Download release: https://github.com/mheryerznkanyan/ios-test-automator-v2/releases/tag/v2.0.0-pilot
2. Follow README instructions
3. Run locally with Docker

**Pros:** 
- Users control their own environment
- No hosting costs for you
- Works offline

**Cons:**
- Requires Docker knowledge
- Users need their own Anthropic API key

---

### Method 2: Hosted Demo (For Sales)

**Setup:**
- Deploy to DigitalOcean/Heroku
- Give users a demo URL
- They upload their iOS app source (or connect via Git)

**Pros:**
- Zero setup for users
- You control the experience

**Cons:**
- Hosting costs (~$12-50/mo)
- You handle support/uptime
- Security concerns (users upload source code)

---

### Method 3: Installation Script (Best UX)

Create a one-liner install:

```bash
curl -fsSL https://testara.dev/install.sh | bash
```

**install.sh does:**
- Check prerequisites (Docker, Python)
- Download latest release
- Set up .env interactively
- Run initial indexing
- Start services

**Pros:**
- Best user experience
- One command to install
- Can update easily

**Cons:**
- Need to host install.sh somewhere
- More work upfront

---

## What I Recommend for Pilot

### For Now (Week 1-2): GitHub Release

**Setup:**
1. Create GitHub release notes (I'll draft)
2. Users clone repo → run Docker
3. You provide 1-on-1 onboarding calls

**Why:**
- Fast to ship
- No hosting costs
- Technical users can handle it

---

### For Scale (After Pilots): Hosted SaaS

**Setup:**
1. Deploy backend + UI to cloud
2. Add user auth (email/password)
3. Charge $100/mo per team
4. Users access via testara.dev

**Why:**
- Non-technical users can use it
- Recurring revenue
- Easier to support

---

## Next Steps (Do This Now)

### 1. Commit Docker Files
```bash
cd /home/openclaw/.openclaw/workspace/ios-test-automator-v2
git add docker-compose.yml Dockerfile.backend Dockerfile.ui DEPLOYMENT.md
git commit -m "feat: add Docker deployment setup"
git push origin main
```

### 2. Test Docker Build Locally
```bash
# Build images
docker-compose build

# Test run
docker-compose up
```

### 3. Create GitHub Release Notes

I'll draft release notes that users can follow to install.

---

## Support for Pilot Users

**Provide:**
- GitHub README with installation steps
- Discord/Slack for questions
- 15-min onboarding call per pilot user

**Expected issues:**
- Docker not installed → send Docker Desktop link
- Anthropic API key issues → guide them through signup
- iOS app path wrong → show them how to find it

---

**Want me to:**
1. Draft the GitHub release notes?
2. Create the install.sh script?
3. Build Docker images and test them?
