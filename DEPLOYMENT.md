# Testara Deployment Guide

Complete guide for deploying Testara locally or in production.

---

## 🚀 Quick Start (Local Development)

### Prerequisites

- **macOS** (for iOS Simulator)
- **Python 3.11+**
- **Node.js 18+** 
- **Xcode** with Command Line Tools
- **Anthropic API key**

### Installation

```bash
# 1. Clone repository
git clone https://github.com/mheryerznkanyan/testara.git
cd testara

# 2. Run setup script
./setup.sh
```

The setup script will:
- ✅ Check prerequisites
- ✅ Install Python dependencies
- ✅ Create `.env` configuration
- ✅ Optionally index your iOS app

### Manual Setup

If you prefer manual installation:

```bash
# 1. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r backend/requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your settings

# 4. Index iOS app
python3 -m rag.cli ingest \
  --app-dir /path/to/your/ios/app \
  --persist ./rag_store \
  --collection ios_app

# 5. Generate app context
python3 generate_app_context.py
```

### Running Services

#### Backend API

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

Access at: http://localhost:8000  
API docs: http://localhost:8000/docs

#### Frontend UI (Optional)

```bash
cd frontend
npm install
npm run dev
```

Access at: http://localhost:3000

---

## 🐳 Docker Deployment

### Quick Start

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

**Services:**
- Backend: http://localhost:8000
- Frontend: http://localhost:3000

### First-Time Setup

**1. Index your iOS app inside container:**

```bash
docker-compose exec backend python -m rag.cli ingest \
  --app-dir /app/ios-app \
  --persist /app/rag_store \
  --collection ios_app
```

**2. Generate app context:**

```bash
docker-compose exec backend python generate_app_context.py
```

### Configuration

**Create `.env` file:**

```bash
# Required
ANTHROPIC_API_KEY=your_key_here

# iOS App Settings
PROJECT_ROOT=/path/to/your/ios/app
XCODE_PROJECT=/path/to/YourApp.xcodeproj
XCODE_SCHEME=YourApp
XCODE_UI_TEST_TARGET=YourAppUITests

# Optional
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929
RAG_PERSIST_DIR=./rag_store
RAG_COLLECTION=ios_app
PORT=8000
```

### Docker Compose Services

**`docker-compose.yml` includes:**

- **backend** — FastAPI server (port 8000)
- **frontend** — Next.js UI (port 3000)

### Stopping Services

```bash
# Stop services
docker-compose stop

# Stop and remove containers
docker-compose down

# Remove volumes too
docker-compose down -v
```

---

## ☁️ Cloud Deployment

### Option 1: DigitalOcean App Platform

**Easiest managed option**

1. Fork repository to your GitHub
2. Create new App on DigitalOcean
3. Connect your forked repo
4. Set environment variables
5. Deploy

**Environment variables needed:**
```
ANTHROPIC_API_KEY
PROJECT_ROOT
```

**Cost:** ~$12-25/month

### Option 2: AWS/GCP

**Using Docker Compose:**

1. Launch EC2/Compute Engine instance
2. Install Docker and Docker Compose
3. Clone repository
4. Configure `.env`
5. Run `docker-compose up -d`

**Cost:** ~$10-50/month depending on instance size

### Option 3: Vercel (Frontend Only)

**Deploy Next.js frontend to Vercel:**

```bash
cd frontend
vercel --prod
```

**Configure environment:**
- Set `NEXT_PUBLIC_API_URL` to your backend URL

**Backend must be deployed separately**

---

## 🔒 Production Checklist

Before deploying to production:

### Security

- [ ] Use HTTPS (SSL/TLS certificates)
- [ ] Rotate API keys regularly
- [ ] Implement rate limiting
- [ ] Add authentication if multi-user
- [ ] Restrict CORS origins
- [ ] Use secrets management (not `.env` files)

### Performance

- [ ] Enable production mode (`npm run build` for frontend)
- [ ] Configure proper logging
- [ ] Set up monitoring (health checks)
- [ ] Optimize RAG index size
- [ ] Configure autoscaling if needed

### Reliability

- [ ] Set up backups (RAG store)
- [ ] Configure restart policies (Docker)
- [ ] Implement error tracking (Sentry)
- [ ] Document recovery procedures
- [ ] Test failover scenarios

---

## 📊 Monitoring

### Health Checks

**Backend:**
```bash
curl http://localhost:8000/health
```

**Expected response:**
```json
{
  "status": "ok",
  "llm_configured": true
}
```

### Logs

**Docker:**
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
```

**Local:**
```bash
# Backend logs (stdout)
cd backend
uvicorn app.main:app --log-level info
```

---

## 🔄 Updates

### Updating Testara

```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r backend/requirements.txt
cd frontend && npm install

# Restart services
docker-compose restart
# or manually restart backend/frontend
```

### Re-indexing After Code Changes

```bash
# Re-index iOS app
python3 -m rag.cli ingest \
  --app-dir /path/to/your/ios/app \
  --persist ./rag_store \
  --collection ios_app

# Regenerate app context
python3 generate_app_context.py

# Restart backend
docker-compose restart backend
```

---

## 🐛 Troubleshooting

### Backend Won't Start

**Check Python version:**
```bash
python3 --version  # Should be 3.11+
```

**Check dependencies:**
```bash
pip install -r backend/requirements.txt
```

**Check .env file:**
```bash
cat .env | grep ANTHROPIC_API_KEY
```

### Frontend Won't Connect

**Check backend is running:**
```bash
curl http://localhost:8000/health
```

**Check API proxy configuration:**
```bash
cat frontend/next.config.js
```

### Docker Issues

**Rebuild images:**
```bash
docker-compose build --no-cache
```

**Check logs:**
```bash
docker-compose logs backend
```

**Reset everything:**
```bash
docker-compose down -v
docker-compose up -d
```

---

## 📞 Support

**Issues:** https://github.com/mheryerznkanyan/testara/issues  
**Discussions:** https://github.com/mheryerznkanyan/testara/discussions

---

## 📝 Configuration Reference

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | ✅ | - | Anthropic API key |
| `ANTHROPIC_MODEL` | ❌ | `claude-sonnet-4-5-20250929` | Claude model to use |
| `PROJECT_ROOT` | ✅ | - | Path to iOS app |
| `XCODE_PROJECT` | ✅ | - | Path to .xcodeproj |
| `XCODE_SCHEME` | ✅ | - | Xcode scheme name |
| `RAG_PERSIST_DIR` | ❌ | `./rag_store` | RAG index location |
| `RAG_COLLECTION` | ❌ | `ios_app` | Collection name |
| `PORT` | ❌ | `8000` | Backend port |

---

Made with ⚡ by Testara
