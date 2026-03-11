# Validation Test Plan

**Branch:** `validation-tests`  
**Purpose:** Verify Testara works end-to-end before pilot launch

---

## 🎯 Test Objectives

Validate that:
1. ✅ RAG extracts correct accessibility IDs from Swift code
2. ✅ Navigation service detects screens and entry points
3. ✅ Description enrichment improves vague inputs
4. ✅ Test generation produces compilable Swift code
5. ✅ Generated tests run on simulator without crashes
6. ✅ Video recording captures test execution

---

## 📋 Test Scenarios

### Scenario 1: Simple Login Test (Baseline)
**Input:** "test login"  
**Expected:**
- Enrichment expands to: "Test that a user can log in with valid credentials..."
- RAG finds: `emailTextField`, `passwordTextField`, `loginButton`
- Navigation detects: LoginView is entry point
- Generated test compiles
- Test runs and passes (or has clear failure reason)

---

### Scenario 2: Navigation Test (Complex)
**Input:** "test tapping items tab"  
**Expected:**
- Navigation service detects: TabView with Items, Profile tabs
- Generated test includes: tab navigation logic
- RAG finds: `itemsTab`, `profileTab` identifiers
- Test compiles and runs

---

### Scenario 3: List Interaction Test (Edge Case)
**Input:** "test tapping first item in the list"  
**Expected:**
- RAG finds: List accessibility IDs
- Generated code uses: `app.cells.element(boundBy: 0)` NOT `app.tables`
- Test compiles and runs

---

### Scenario 4: Error Handling Test (Validation)
**Input:** "test login with wrong password shows error"  
**Expected:**
- Generated test includes: invalid credentials
- Assertion checks for error message element
- Test runs and validates error state

---

### Scenario 5: Search Test (System UI)
**Input:** "test searching for an item"  
**Expected:**
- Generated code uses: `app.searchFields.firstMatch`
- Search field interaction works
- Test compiles

---

## 🧪 How to Run

### Prerequisites
```bash
# 1. Backend running
cd backend
source venv/bin/activate  # or use uv
python -m uvicorn app.main:app --reload

# 2. RAG vector store indexed
python -m rag.cli ingest --app-dir /path/to/ios-app --persist ./rag_store --collection ios_app

# 3. .env configured
cat > .env << EOF
ANTHROPIC_API_KEY=your_key_here
PROJECT_ROOT=/path/to/ios-app
EOF
```

### Run Validation Tests
```bash
# Option A: Run all validation tests
pytest tests/validation/ -v

# Option B: Run specific scenario
pytest tests/validation/test_end_to_end.py::test_login_generation -v

# Option C: Interactive validation (manual)
python tests/validation/manual_validation.py
```

---

## 📊 Success Criteria

### ✅ **PASS Criteria:**
- [ ] All 5 scenarios generate valid Swift code (syntax check passes)
- [ ] 4/5 scenarios produce tests that compile in Xcode
- [ ] 3/5 scenarios produce tests that run on simulator
- [ ] RAG context retrieval works for 100% of scenarios
- [ ] Navigation service correctly identifies entry point
- [ ] Enrichment improves vague descriptions in all cases

### ❌ **FAIL Criteria:**
- Any scenario crashes the backend
- Generated code has syntax errors
- RAG returns empty context for indexed app
- Navigation service fails to detect any screens

---

## 🐛 Known Issues to Watch For

1. **Armenian keyboard switching** (should be fixed now)
2. **SwiftUI List access** (should use `app.cells`, not `app.tables`)
3. **Missing waits** (tests should include `waitForExistence`)
4. **Hardcoded data values** (should avoid unless certain)
5. **Missing springboard alert handling** (password save popups)

---

## 📝 Test Results Template

```markdown
## Test Run: [Date]

### Scenario 1: Simple Login Test
- ✅ Enrichment: PASS
- ✅ RAG context: PASS (found emailTextField, passwordTextField, loginButton)
- ✅ Navigation: PASS (detected LoginView as entry)
- ✅ Code generation: PASS (compiles)
- ✅ Execution: PASS (test ran, recorded video)

### Scenario 2: Navigation Test
- ✅ Enrichment: PASS
- ❌ RAG context: FAIL (missed itemsTab identifier)
- ...

### Overall: 4/5 PASS
```

---

## 🚀 After Validation

If tests pass:
1. Merge `validation-tests` → `main` (keep tests for regression)
2. Tag release: `v2.0.0-pilot`
3. Start pilot outreach

If tests fail:
1. Fix issues on `validation-tests` branch
2. Re-run validation
3. Merge when green
