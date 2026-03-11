#!/bin/bash
# Run Testara validation tests
# Usage: ./run_validation.sh [auto|manual|all]

set -e

MODE="${1:-all}"

echo "🚀 Testara Validation Suite"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check prerequisites
echo ""
echo "🔍 Checking prerequisites..."

# Check if backend is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ Backend not running"
    echo ""
    echo "Start backend with:"
    echo "  cd backend && uvicorn app.main:app --reload"
    exit 1
fi
echo "✅ Backend is running"

# Check RAG store
RAG_STATUS=$(curl -s http://localhost:8000/rag/status 2>/dev/null)
if echo "$RAG_STATUS" | grep -q '"status":"ok"'; then
    DOC_COUNT=$(echo "$RAG_STATUS" | grep -o '"document_count":[0-9]*' | grep -o '[0-9]*')
    echo "✅ RAG store indexed ($DOC_COUNT documents)"
else
    echo "❌ RAG store not indexed"
    echo ""
    echo "Index your iOS app with:"
    echo "  python -m rag.cli ingest --app-dir /path/to/ios-app --persist ./rag_store --collection ios_app"
    exit 1
fi

# Check Python dependencies
if ! python3 -c "import pytest, requests" 2>/dev/null; then
    echo "❌ Missing dependencies"
    echo ""
    echo "Install with:"
    echo "  pip install pytest requests"
    exit 1
fi
echo "✅ Dependencies installed"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Run tests based on mode
case "$MODE" in
    auto)
        echo ""
        echo "🤖 Running automated tests..."
        echo ""
        pytest tests/validation/test_end_to_end.py -v --tb=short
        ;;
    manual)
        echo ""
        echo "👤 Running manual validation..."
        echo ""
        python tests/validation/manual_validation.py
        ;;
    all)
        echo ""
        echo "🤖 Running automated tests first..."
        echo ""
        if pytest tests/validation/test_end_to_end.py -v --tb=short; then
            echo ""
            echo "✅ Automated tests passed!"
            echo ""
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo ""
            echo "👤 Now running manual validation..."
            echo ""
            python tests/validation/manual_validation.py
        else
            echo ""
            echo "❌ Automated tests failed — fix issues before manual validation"
            exit 1
        fi
        ;;
    *)
        echo "❌ Invalid mode: $MODE"
        echo ""
        echo "Usage: ./run_validation.sh [auto|manual|all]"
        echo ""
        echo "  auto   - Run automated pytest tests only"
        echo "  manual - Run interactive manual validation only"
        echo "  all    - Run both (default)"
        exit 1
        ;;
esac

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Validation complete"
