#!/bin/bash
set -e

echo "🚀 Testara Setup"
echo "================"
echo ""

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ Error: Testara requires macOS (for iOS Simulator)"
    exit 1
fi

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 not found"
    echo "Install: brew install python3"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
if (( $(echo "$PYTHON_VERSION < 3.11" | bc -l) )); then
    echo "❌ Error: Python 3.11+ required (found $PYTHON_VERSION)"
    exit 1
fi

# Check Xcode
if ! command -v xcodebuild &> /dev/null; then
    echo "❌ Error: Xcode Command Line Tools not found"
    echo "Install: xcode-select --install"
    exit 1
fi

echo "✅ Prerequisites OK"
echo ""

# Install Python dependencies
echo "📦 Installing Python dependencies..."
python3 -m pip install --upgrade pip
pip3 install -r backend/requirements.txt

echo "✅ Dependencies installed"
echo ""

# Setup configuration
if [ ! -f .env ]; then
    echo "⚙️  Setting up configuration..."
    cp .env.example .env
    
    echo ""
    echo "Please configure your .env file:"
    echo "1. Add your ANTHROPIC_API_KEY"
    echo "2. Set PROJECT_ROOT to your iOS app path"
    echo "3. Configure XCODE_PROJECT and XCODE_SCHEME"
    echo ""
    read -p "Open .env now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ${EDITOR:-nano} .env
    fi
else
    echo "✅ .env already exists"
fi

echo ""

# Ask if user wants to index now
echo "📊 RAG Indexing"
echo "=============="
echo ""
echo "Do you want to index your iOS app now?"
echo "This analyzes your code to generate better tests."
echo ""
read -p "Index now? (y/n) " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Load PROJECT_ROOT from .env
    if [ -f .env ]; then
        export $(grep -v '^#' .env | xargs)
    fi
    
    if [ -z "$PROJECT_ROOT" ]; then
        echo ""
        read -p "Enter path to your iOS app: " PROJECT_ROOT
    fi
    
    if [ ! -d "$PROJECT_ROOT" ]; then
        echo "❌ Error: Directory not found: $PROJECT_ROOT"
        exit 1
    fi
    
    echo "🔍 Indexing $PROJECT_ROOT ..."
    python3 -m rag.cli ingest \
        --app-dir "$PROJECT_ROOT" \
        --persist ./rag_store \
        --collection ios_app
    
    echo ""
    echo "🎯 Generating app context..."
    python3 generate_app_context.py
    
    echo "✅ Indexing complete"
else
    echo "⏭  Skipping indexing (run later: python3 -m rag.cli ingest ...)"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "🚀 Next steps:"
echo ""
echo "1. Start backend:"
echo "   cd backend && uvicorn app.main:app --reload --port 8000"
echo ""
echo "2. (Optional) Start frontend:"
echo "   cd frontend && npm install && npm run dev"
echo ""
echo "3. Generate your first test:"
echo "   curl -X POST http://localhost:8000/generate-test-with-rag \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"description\": \"Test login with valid credentials\"}'"
echo ""
