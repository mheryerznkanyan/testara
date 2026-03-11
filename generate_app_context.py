#!/usr/bin/env python3
"""Generate APP_CONTEXT.md from indexed codebase"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.core.config import settings
from app.services.rag_service import RAGService
from app.services.context_extractor import AppContextExtractor


def main():
    """Generate APP_CONTEXT.md from RAG index"""
    print("🔍 Extracting app context from indexed codebase...")
    
    # Initialize services
    rag_service = RAGService(settings=settings)
    extractor = AppContextExtractor(rag_service)
    
    # Generate and save
    output_path = Path(__file__).parent / "APP_CONTEXT.md"
    
    success = extractor.save_to_file(str(output_path))
    
    if success:
        print(f"✅ Generated: {output_path}")
        print("\n📄 Preview:")
        print("-" * 60)
        with open(output_path, 'r') as f:
            preview = f.read()[:500]
            print(preview)
            if len(preview) >= 500:
                print("...\n(truncated)")
        print("-" * 60)
        print("\n✨ APP_CONTEXT.md is ready!")
        print("   Edit it to add more details (credentials, flows, etc.)")
    else:
        print("❌ Failed to generate app context")
        print("   Make sure your code is indexed: python -m rag.cli index <path>")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
