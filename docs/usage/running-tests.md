# Running Tests

Execute generated tests in the iOS simulator.

## Via Web UI

1. After generating a test, click **Run Test**
2. Wait for build and execution
3. View results and video recording

## Via API

```bash
curl -X POST http://localhost:8000/run-test \
  -H "Content-Type: application/json" \
  -d '{
    "test_code": "...",
    "class_name": "LoginTests",
    "method_name": "testLogin"
  }'
```

## Manual Execution in Xcode

1. Open your Xcode project
2. Navigate to your UI test target
3. Find `LLMGeneratedTest.swift`
4. Click the diamond icon next to the test method
5. Test runs in simulator

## Test Results

Results include:

- **Pass/Fail status**
- **Execution time**
- **Video recording**
- **Console logs**
- **Screenshots** (on failure)

*Full guide coming soon.*
