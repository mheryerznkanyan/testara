"""End-to-end validation tests for Testara.

Tests the full pipeline: description → enrichment → RAG → generation → Swift output.
Does NOT run tests on simulator (that's manual validation).
"""
import pytest
import requests
from pathlib import Path


# Base URL for backend API
BASE_URL = "http://localhost:8000"


def test_backend_health():
    """Verify backend is running and healthy."""
    response = requests.get(f"{BASE_URL}/health", timeout=5)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["llm_configured"] is True


def test_rag_status():
    """Verify RAG vector store is indexed and accessible."""
    response = requests.get(f"{BASE_URL}/rag/status", timeout=5)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["document_count"] > 0, "RAG store is empty — run indexing first"


@pytest.mark.parametrize("description,test_type,expected_identifiers", [
    (
        "test login",
        "ui",
        ["emailTextField", "passwordTextField", "loginButton"]
    ),
    (
        "test tapping items tab",
        "ui",
        ["itemsTab", "Items"]
    ),
    (
        "test tapping first item shows detail",
        "ui",
        ["cells", "element(boundBy: 0)"]
    ),
])
def test_generate_with_rag(description, test_type, expected_identifiers):
    """Test RAG-powered generation for common scenarios."""
    payload = {
        "test_description": description,
        "test_type": test_type,
        "include_comments": True,
    }
    
    response = requests.post(
        f"{BASE_URL}/generate-test-with-rag",
        json=payload,
        timeout=60
    )
    
    assert response.status_code == 200, f"Generation failed: {response.text}"
    data = response.json()
    
    # Validate response structure
    assert "swift_code" in data
    assert "test_type" in data
    assert "class_name" in data
    assert "metadata" in data
    
    swift_code = data["swift_code"]
    metadata = data["metadata"]
    
    # Check enrichment happened
    assert metadata.get("enrichment", {}).get("enrichment_used") is True
    
    # Check RAG context was retrieved
    rag_context = metadata.get("rag_context", {})
    assert rag_context.get("total_docs_retrieved", 0) > 0
    
    # Check Swift code contains expected patterns
    assert "import XCTest" in swift_code
    assert "XCUIApplication()" in swift_code
    assert "app.launch()" in swift_code
    assert "waitForExistence" in swift_code
    
    # Check for expected accessibility IDs from RAG
    for identifier in expected_identifiers:
        assert identifier in swift_code, f"Expected identifier '{identifier}' not found in generated code"
    
    # Check for best practices
    assert 'launchArguments = ["-AppleLanguages"' in swift_code, "Missing locale args"
    assert "XCTAssert" in swift_code, "Missing assertions"


def test_navigation_context_injection():
    """Test that navigation context is injected when PROJECT_ROOT is set."""
    payload = {
        "test_description": "test navigating to profile screen",
        "test_type": "ui",
    }
    
    response = requests.post(
        f"{BASE_URL}/generate-test-with-rag",
        json=payload,
        timeout=60
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check navigation metadata
    nav_metadata = data["metadata"].get("navigation", {})
    if nav_metadata.get("navigation_context_used"):
        # If navigation was extracted, generated code should include login steps
        # (since profile typically requires login)
        swift_code = data["swift_code"]
        # Should have login-related code or explicit navigation
        assert any(word in swift_code.lower() for word in ["login", "email", "password", "profiletab", "tab"])


def test_enrichment_improves_description():
    """Test that vague descriptions get enriched."""
    payload = {
        "test_description": "test login",  # vague
        "test_type": "ui",
    }
    
    response = requests.post(
        f"{BASE_URL}/generate-test-with-rag",
        json=payload,
        timeout=60
    )
    
    assert response.status_code == 200
    data = response.json()
    
    enrichment = data["metadata"]["enrichment"]
    original = enrichment["original_description"]
    enriched = enrichment["enriched_description"]
    
    # Enriched should be longer and more specific
    assert len(enriched) > len(original)
    assert "test login" in original.lower()
    # Enriched should mention specifics like fields, buttons, credentials
    assert any(word in enriched.lower() for word in ["email", "password", "field", "button", "tap"])


def test_batch_generation_limit():
    """Test that batch endpoint respects size limit."""
    # Try to generate 21 tests (over default limit of 20)
    payloads = [
        {"test_description": f"test scenario {i}", "test_type": "ui"}
        for i in range(21)
    ]
    
    response = requests.post(
        f"{BASE_URL}/generate-tests-batch",
        json=payloads,
        timeout=5
    )
    
    # Should reject with 400
    assert response.status_code == 400
    assert "exceeds the maximum" in response.json()["detail"]


def test_invalid_test_type():
    """Test that invalid test_type is rejected."""
    payload = {
        "test_description": "test something",
        "test_type": "invalid",
    }
    
    response = requests.post(
        f"{BASE_URL}/generate-test-with-rag",
        json=payload,
        timeout=10
    )
    
    assert response.status_code == 400
    assert "test_type must be" in response.json()["detail"]


def test_swift_code_syntax_validity():
    """Test that generated code has valid Swift syntax markers."""
    payload = {
        "test_description": "test login with valid credentials",
        "test_type": "ui",
    }
    
    response = requests.post(
        f"{BASE_URL}/generate-test-with-rag",
        json=payload,
        timeout=60
    )
    
    assert response.status_code == 200
    swift_code = response.json()["swift_code"]
    
    # Check basic Swift syntax
    assert swift_code.count("{") == swift_code.count("}"), "Unbalanced braces"
    assert swift_code.count("(") == swift_code.count(")"), "Unbalanced parentheses"
    
    # Check for common syntax errors
    assert "```" not in swift_code, "Markdown code fences in output"
    assert not swift_code.startswith("Here"), "LLM explanation instead of code"
    
    # Check structure
    assert "class " in swift_code or "final class" in swift_code
    assert ": XCTestCase" in swift_code
    assert "func test" in swift_code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
