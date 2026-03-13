# Installation

Detailed installation guide for Testara.

## System Requirements

- **macOS** 12.0+ (Monterey or later)
- **Xcode** 15.0+
- **Python** 3.11+
- **Node.js** 20.0+
- **Git**

## Step-by-Step Installation

### 1. Install Prerequisites

#### Python 3.11+

```bash
# Check if Python 3.11+ is installed
python3 --version

# If not, install via Homebrew
brew install python@3.11
```

#### Node.js 20+

```bash
# Check if Node.js is installed
node --version

# If not, install via Homebrew
brew install node@20
```

### 2. Clone Repository

```bash
git clone https://github.com/mheryerznkanyan/testara.git
cd testara
```

### 3. Install Python Dependencies

```bash
# Install in development mode
pip install -e .

# Or install with docs dependencies
pip install -e ".[docs]"
```

### 4. Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

### 5. Get Anthropic API Key

1. Visit [console.anthropic.com](https://console.anthropic.com/)
2. Sign up or log in
3. Navigate to API Keys
4. Create a new key
5. Copy the key

### 6. Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:

```bash
ANTHROPIC_API_KEY=your_key_here
PROJECT_ROOT=/absolute/path/to/your/ios/app
```

## Verification

### Check Installation

```bash
# Backend
python -c "import fastapi; print('FastAPI installed')"
python -c "import langchain; print('LangChain installed')"

# Frontend
cd frontend && npm run build && cd ..
```

### Start Services

```bash
./start.sh
```

You should see:
- ✅ Backend running on http://localhost:8000
- ✅ Frontend running on http://localhost:3000

## Alternative Installation Methods

### Using Docker

See [Docker Deployment Guide](../advanced/docker.md)

### Using Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e .
```

## Troubleshooting

### Python Version Issues

!!! bug "Python 3.10 or older"
    Testara requires Python 3.11+. Install the latest version:
    ```bash
    brew install python@3.11
    ```

### Missing Xcode

!!! bug "Xcode not found"
    Install Xcode from the Mac App Store, then:
    ```bash
    sudo xcode-select --install
    ```

### Permission Errors

!!! bug "Permission denied"
    Don't use `sudo` with pip. Use a virtual environment instead:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -e .
    ```

## Next Steps

- [Configure your environment](configuration.md)
- [Start generating tests](../usage/generating-tests.md)
