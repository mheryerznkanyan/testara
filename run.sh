#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"
APP_DIR="${1:-/Users/mheryerznkanyan/Projects/iOS-test-automator/ios-app/src/SampleApp}"

# ---------- 1. Virtual environment ----------
if [ ! -d "$VENV_DIR" ]; then
  echo ">>> Creating virtual environment..."
  python3 -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"

# ---------- 2. Install dependencies ----------
echo ">>> Installing dependencies..."
pip install -q -e "$PROJECT_DIR"

# ---------- 3. Ingest Swift project into RAG store ----------
echo ">>> Ingesting $APP_DIR into vector store..."
python -m rag.cli ingest \
  --app-dir "$APP_DIR" \
  --persist "$PROJECT_DIR/rag_store" \
  --collection ios_app

# ---------- 4. Start backend + Streamlit UI ----------
echo ">>> Starting backend on port 8000..."
cd "$PROJECT_DIR/backend"
uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!

echo ">>> Starting Streamlit UI..."
cd "$PROJECT_DIR"
streamlit run ui/app.py &
UI_PID=$!

# ---------- Cleanup on exit ----------
cleanup() {
  echo ""
  echo ">>> Shutting down..."
  kill "$BACKEND_PID" "$UI_PID" 2>/dev/null || true
  wait "$BACKEND_PID" "$UI_PID" 2>/dev/null || true
  echo ">>> Done."
}
trap cleanup EXIT INT TERM

echo ""
echo "========================================="
echo "  Backend:   http://localhost:8000"
echo "  UI:        http://localhost:8501"
echo "  Press Ctrl+C to stop"
echo "========================================="

wait
