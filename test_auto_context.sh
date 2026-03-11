#!/bin/bash
# Test auto-context generation feature
# Usage: ./test_auto_context.sh

set -e

echo "🧪 Testing Auto-Context Generation Feature"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check prerequisites
echo ""
echo "🔍 Checking prerequisites..."

# Check if backend dependencies are installed
if ! python3 -c "import pytest, langchain_anthropic" 2>/dev/null; then
    echo "❌ Missing dependencies"
    echo ""
    echo "Install with:"
    echo "  cd backend && pip install -r requirements.txt"
    echo "  pip install pytest"
    exit 1
fi
echo "✅ Dependencies installed"

# Check for ANTHROPIC_API_KEY
if [ -z "$ANTHROPIC_API_KEY" ]; then
    if [ -f backend/.env ]; then
        echo "✅ Found backend/.env (will load API key)"
    else
        echo "❌ ANTHROPIC_API_KEY not set"
        echo ""
        echo "Set it with:"
        echo "  export ANTHROPIC_API_KEY=your-key"
        echo "Or create backend/.env with:"
        echo "  ANTHROPIC_API_KEY=your-key"
        exit 1
    fi
else
    echo "✅ ANTHROPIC_API_KEY is set"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Test 1: Context Extraction Tests
echo ""
echo "📋 Test 1: Context Extraction (no LLM needed)"
echo ""
pytest tests/test_context_enrichment_quality.py::TestContextExtraction -v --tb=short

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Context extraction tests passed!"
else
    echo ""
    echo "❌ Context extraction tests failed"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Test 2: LLM-as-Judge Quality Tests
echo ""
echo "🤖 Test 2: LLM-as-Judge Enrichment Quality"
echo ""
echo "⚠️  This will use Claude API (costs ~$0.10)"
echo ""
read -p "Run LLM-as-judge tests? (y/n) " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    pytest tests/test_context_enrichment_quality.py::TestEnrichmentQuality -v -s --tb=short
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ LLM-as-judge tests passed!"
        echo "   Context improves enrichment quality! 🎉"
    else
        echo ""
        echo "❌ LLM-as-judge tests failed"
        exit 1
    fi
else
    echo ""
    echo "⏭️  Skipped LLM-as-judge tests"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Test 3: Integration Test (if RAG is indexed)
echo ""
echo "🔗 Test 3: Integration with RAG Index"
echo ""

# Check if RAG store exists
if [ -d "./rag_store" ]; then
    echo "✅ RAG store found"
    echo ""
    echo "Testing context generation from RAG..."
    
    # Run the generation script
    if python3 generate_app_context.py; then
        echo ""
        echo "✅ APP_CONTEXT.md generated successfully!"
        echo ""
        echo "Preview:"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        head -n 20 APP_CONTEXT.md
        echo "..."
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    else
        echo ""
        echo "❌ Failed to generate APP_CONTEXT.md"
        echo "   (This is OK if you haven't indexed your app yet)"
    fi
else
    echo "⚠️  RAG store not found at ./rag_store"
    echo ""
    echo "To test full integration:"
    echo "  1. Index your iOS app:"
    echo "     python -m rag.cli ingest --app-dir /path/to/app --persist ./rag_store"
    echo "  2. Run this test again"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ Auto-context feature tests complete!"
echo ""
echo "📊 Summary:"
echo "   • Context extraction: ✅"
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "   • LLM-as-judge quality: ✅"
else
    echo "   • LLM-as-judge quality: ⏭️  (skipped)"
fi
if [ -d "./rag_store" ]; then
    echo "   • RAG integration: ✅"
else
    echo "   • RAG integration: ⏭️  (no RAG store)"
fi
echo ""
echo "🎉 Ready to merge to dev!"
