#!/bin/bash
set -e

cd "$(dirname "$0")"

# Check macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "Error: Testara requires macOS (for iOS Simulator)"
    exit 1
fi

# Find Python 3.11+
PYTHON=""
for py in python3.13 python3.12 python3.11; do
    if command -v $py &> /dev/null; then
        PYTHON=$py
        break
    fi
done
if [ -z "$PYTHON" ]; then
    echo "Error: Python 3.11+ required. Install with: brew install python@3.11"
    exit 1
fi
echo "Using $($PYTHON --version)"

# Check other prerequisites
for cmd in node xcodebuild; do
    if ! command -v $cmd &> /dev/null; then
        echo "Error: $cmd not found"
        exit 1
    fi
done

# Check .env
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env from .env.example"
    echo "Please edit .env and set ANTHROPIC_API_KEY and PROJECT_ROOT, then re-run."
    exit 1
fi

# Create/activate virtual environment
VENV_DIR=".venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    $PYTHON -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"

# Install dependencies
echo "Installing backend dependencies..."
pip install -e . --quiet

echo "Installing frontend dependencies..."
cd frontend && npm install --silent && cd ..

# Start backend
echo "Starting backend on port 8000..."
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Start frontend
echo "Starting frontend on port 8501..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "Testara is running!"
echo "  Frontend: http://localhost:8501"
echo "  API:      http://localhost:8000"
echo ""

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
