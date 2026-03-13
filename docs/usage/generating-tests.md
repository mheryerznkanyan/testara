# Generating Tests

Learn how to generate iOS tests with Testara.

## Basic Usage

### Via Web UI

1. **Open the frontend:** http://localhost:3000

2. **Enter test description:**
   ```
   test login with invalid password shows error
   ```

3. **Click Generate**

4. **Copy the generated code**

### Via API

```bash
curl -X POST http://localhost:8000/generate-test-with-rag \
  -H "Content-Type: application/json" \
  -d '{"description": "test login with invalid password"}'
```

## Writing Good Test Descriptions

### ✅ Good Examples

**Specific and actionable:**
```
test login with valid credentials navigates to home screen
```

**Includes expected outcome:**
```
test adding item to cart updates badge count
```

**Mentions navigation:**
```
test tapping profile tab shows user settings
```

### ❌ Bad Examples

**Too vague:**
```
test the app
```

**Missing context:**
```
test button
```

**No clear outcome:**
```
test login
```

## Test Description Patterns

### Login/Auth Tests

```
test login with valid credentials succeeds
test login with invalid email shows error
test logout clears user session
test forgot password sends reset email
```

### Navigation Tests

```
test tapping home tab shows home screen
test back button returns to previous screen
test deep link opens correct screen
```

### Form Tests

```
test submitting empty form shows validation errors
test entering valid data enables submit button
test canceling form discards changes
```

### List/Collection Tests

```
test scrolling to bottom loads more items
test tapping item shows detail view
test pulling to refresh updates list
test search filters results correctly
```

## Advanced Features

### Test with Prerequisites

Describe the setup needed:

```
after logging in, test adding item to wishlist shows confirmation
```

### Test Multiple States

```
test toggling dark mode updates theme throughout app
```

### Test Error Handling

```
test network failure shows retry button
```

## Understanding Generated Code

Generated tests include:

1. **Setup code** — App launch configuration
2. **Element queries** — Using accessibility identifiers
3. **Interactions** — Taps, text entry, swipes
4. **Assertions** — Verify expected outcomes
5. **Waits** — Proper synchronization

Example:

```swift
import XCTest

final class LoginTests: XCTestCase {
    func testLoginWithInvalidPassword() throws {
        // 1. Setup
        let app = XCUIApplication()
        app.launchArguments = ["-AppleLanguages", "(en)"]
        app.launch()
        
        // 2. Element queries
        let emailField = app.textFields["emailTextField"]
        XCTAssertTrue(emailField.waitForExistence(timeout: 5))
        
        // 3. Interactions
        emailField.tap()
        emailField.typeText("user@test.com")
        
        // 4. Assertions
        let errorLabel = app.staticTexts["errorLabel"]
        XCTAssertTrue(errorLabel.waitForExistence(timeout: 5))
    }
}
```

## Next Steps

- [Run tests](running-tests.md)
- [Understand the RAG pipeline](rag-indexing.md)
- [Customize test generation](../advanced/customization.md)
