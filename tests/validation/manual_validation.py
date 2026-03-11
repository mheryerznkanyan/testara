#!/usr/bin/env python3
"""Interactive manual validation script for Testara.

Walks through key scenarios step-by-step, generates tests, and guides you through
running them on the simulator.
"""
import os
import sys
from pathlib import Path

import requests


BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

SCENARIOS = [
    {
        "name": "Simple Login Test",
        "description": "test login",
        "expected_elements": ["emailTextField", "passwordTextField", "loginButton"],
        "notes": "Should include login flow, proper waits, assertions",
    },
    {
        "name": "Tab Navigation",
        "description": "test tapping profile tab",
        "expected_elements": ["profileTab", "tab"],
        "notes": "Should navigate to tab and verify screen loaded",
    },
    {
        "name": "List Interaction",
        "description": "test tapping first item in list",
        "expected_elements": ["cells", "element(boundBy: 0)"],
        "notes": "Should use app.cells, NOT app.tables",
    },
    {
        "name": "Search Test",
        "description": "test searching for an item",
        "expected_elements": ["searchFields", "firstMatch"],
        "notes": "Should use system search field (no custom identifier)",
    },
    {
        "name": "Error Validation",
        "description": "test login with wrong password shows error",
        "expected_elements": ["error", "Invalid", "XCTAssert"],
        "notes": "Should include invalid credentials and error assertion",
    },
]


def check_backend():
    """Check if backend is running."""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=3)
        if response.status_code == 200:
            print("✅ Backend is running")
            return True
        print(f"❌ Backend returned {response.status_code}")
        return False
    except requests.RequestException as e:
        print(f"❌ Backend not reachable: {e}")
        print(f"\nStart backend with:")
        print(f"  cd backend && uvicorn app.main:app --reload")
        return False


def check_rag():
    """Check if RAG store is indexed."""
    try:
        response = requests.get(f"{BASE_URL}/rag/status", timeout=3)
        if response.status_code == 200:
            data = response.json()
            doc_count = data.get("document_count", 0)
            if doc_count > 0:
                print(f"✅ RAG store indexed ({doc_count} documents)")
                return True
            print("❌ RAG store is empty")
            print("\nIndex your iOS app with:")
            print("  python -m rag.cli ingest --app-dir /path/to/ios-app --persist ./rag_store --collection ios_app")
            return False
        print(f"❌ RAG status check failed: {response.status_code}")
        return False
    except requests.RequestException as e:
        print(f"❌ RAG status check failed: {e}")
        return False


def generate_test(description):
    """Generate test using the RAG endpoint."""
    print(f"\n🔄 Generating test for: '{description}'")
    
    payload = {
        "test_description": description,
        "test_type": "ui",
        "include_comments": True,
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/generate-test-with-rag",
            json=payload,
            timeout=60
        )
        
        if response.status_code != 200:
            print(f"❌ Generation failed: {response.status_code}")
            print(response.text)
            return None
        
        data = response.json()
        return data
    except requests.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None


def validate_scenario(scenario):
    """Run validation for a single scenario."""
    print("\n" + "="*60)
    print(f"📋 Scenario: {scenario['name']}")
    print(f"📝 Description: {scenario['description']}")
    print(f"💡 Notes: {scenario['notes']}")
    print("="*60)
    
    data = generate_test(scenario["description"])
    if not data:
        print("❌ FAIL: Generation failed")
        return False
    
    swift_code = data["swift_code"]
    metadata = data["metadata"]
    
    print("\n📊 Generation Metadata:")
    print(f"  - Class: {data['class_name']}")
    print(f"  - Enrichment used: {metadata.get('enrichment', {}).get('enrichment_used', False)}")
    print(f"  - RAG docs retrieved: {metadata.get('rag_context', {}).get('total_docs_retrieved', 0)}")
    print(f"  - Navigation context: {metadata.get('navigation', {}).get('navigation_context_used', False)}")
    
    # Check for expected elements
    print("\n🔍 Checking for expected elements...")
    all_found = True
    for element in scenario["expected_elements"]:
        if element in swift_code:
            print(f"  ✅ Found: {element}")
        else:
            print(f"  ❌ Missing: {element}")
            all_found = False
    
    # Check for best practices
    print("\n🔍 Checking best practices...")
    checks = {
        "Locale args": 'launchArguments = ["-AppleLanguages"' in swift_code,
        "Wait for existence": "waitForExistence" in swift_code,
        "Assertions": "XCTAssert" in swift_code,
        "No code fences": "```" not in swift_code,
    }
    
    for check_name, passed in checks.items():
        if passed:
            print(f"  ✅ {check_name}")
        else:
            print(f"  ❌ {check_name}")
            all_found = False
    
    # Show generated code
    print("\n📄 Generated Swift Code:")
    print("-" * 60)
    print(swift_code[:800])  # First 800 chars
    if len(swift_code) > 800:
        print(f"\n... ({len(swift_code) - 800} more characters)")
    print("-" * 60)
    
    # Ask for manual validation
    print("\n🤔 Manual check:")
    print("  1. Does the code look correct?")
    print("  2. Would it compile in Xcode?")
    print("  3. Does it test what was requested?")
    
    response = input("\n✋ Mark this scenario as PASS? (y/n): ").strip().lower()
    
    if response == 'y':
        print("✅ Scenario PASSED")
        return True
    else:
        print("❌ Scenario FAILED")
        return False


def main():
    """Run interactive validation."""
    print("🚀 Testara Manual Validation")
    print("="*60)
    
    # Preflight checks
    print("\n1️⃣ Checking prerequisites...")
    if not check_backend():
        sys.exit(1)
    if not check_rag():
        sys.exit(1)
    
    # Run scenarios
    print("\n2️⃣ Running validation scenarios...")
    input("\nPress Enter to start validation scenarios...")
    
    results = []
    for scenario in SCENARIOS:
        passed = validate_scenario(scenario)
        results.append((scenario["name"], passed))
        
        if len(results) < len(SCENARIOS):
            input("\nPress Enter for next scenario...")
    
    # Summary
    print("\n" + "="*60)
    print("📊 VALIDATION SUMMARY")
    print("="*60)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {name}")
    
    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)
    
    print(f"\n🎯 Score: {passed_count}/{total_count} scenarios passed")
    
    if passed_count == total_count:
        print("\n✅ ALL SCENARIOS PASSED — Ready for pilot launch!")
    elif passed_count >= total_count * 0.8:
        print("\n⚠️  Most scenarios passed — Review failures and iterate")
    else:
        print("\n❌ VALIDATION FAILED — Fix issues before pilot")
    
    return passed_count == total_count


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
