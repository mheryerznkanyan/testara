# REST API Reference

Testara's HTTP API endpoints.

## Endpoints

### POST /generate-test-with-rag

Generate a test from plain English description.

**Request:**
```json
{
  "description": "test login with valid credentials"
}
```

**Response:**
```json
{
  "test_code": "import XCTest...",
  "class_name": "LoginTests",
  "method_name": "testLogin"
}
```

### POST /run-test

Execute a generated test.

*Full API documentation coming soon.*
