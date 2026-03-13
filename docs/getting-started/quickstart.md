# Quick Start

Get Testara up and running in 5 minutes.

## Prerequisites

!!! info "System Requirements"
    - **macOS** with Xcode installed (required for iOS simulators)
    - **Python 3.11+**
    - **Node.js 20+**
    - Anthropic API key ([get one](https://console.anthropic.com/))
    - Your iOS app source code

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/mheryerznkanyan/testara.git
cd testara
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and set:

```bash
# Required
ANTHROPIC_API_KEY=your_key_here

# Your iOS app
PROJECT_ROOT=/path/to/your/ios/app
```

!!! tip "Getting an Anthropic API Key"
    Visit [console.anthropic.com](https://console.anthropic.com/) to create an account and get your API key.

### 3. Start Services

```bash
./start.sh
```

This will:

- 🎨 Display colorful ASCII art banner
- ✅ Check system requirements
- 📦 Install dependencies
- 🚀 Start backend (port 8000) and frontend (port 3000)
- 📊 Show service status

!!! success "Services Running"
    - **Frontend:** http://localhost:3000
    - **API:** http://localhost:8000

## First Test

### Via Web UI

1. Open http://localhost:3000
2. Enter a test description: `"test login with valid credentials"`
3. Click **Generate**
4. Copy the generated XCUITest code
5. Paste into your Xcode UI test target
6. Run the test!

### Via API

```bash
curl -X POST http://localhost:8000/generate-test-with-rag \
  -H "Content-Type: application/json" \
  -d '{"description": "test login with valid credentials"}'
```

## What's Next?

- [Learn about Configuration](configuration.md)
- [Understand How It Works](../architecture/overview.md)
- [Explore Advanced Features](../advanced/docker.md)

## Troubleshooting

!!! bug "Backend won't start?"
    ```bash
    # Check Python dependencies
    pip install -e .
    ```

!!! bug "Can't connect to frontend?"
    Make sure both services are running:
    
    - Backend: `uvicorn app.main:app --port 8000`
    - Frontend: `npm run dev` (in `frontend/`)

!!! bug "Xcode project not found?"
    Ensure `PROJECT_ROOT` in `.env` points to the directory containing your `.xcodeproj` file.
