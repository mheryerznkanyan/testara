# Validation Tests

**Branch:** `validation-tests`  
**Purpose:** Verify Testara works correctly before pilot launch

---

## Quick Start

```bash
# 1. Start backend
cd backend
uvicorn app.main:app --reload

# 2. Index your iOS app
python -m rag.cli ingest \
  --app-dir /path/to/ios-app \
  --persist ./rag_store \
  --collection ios_app

# 3. Run automated tests
pytest tests/validation/test_end_to_end.py -v

# 4. Run manual validation (interactive)
python tests/validation/manual_validation.py
```

---

## What Gets Tested

### Automated Tests (`test_end_to_end.py`)
✅ Backend health check  
✅ RAG vector store status  
✅ Test generation with RAG  
✅ Navigation context injection  
✅ Description enrichment  
✅ Batch size limits  
✅ Error handling  
✅ Swift syntax validation  

**Run with:** `pytest tests/validation/test_end_to_end.py -v`

---

### Manual Validation (`manual_validation.py`)
Interactive script that walks you through 5 scenarios:

1. **Simple Login Test** — Basic flow with fields + button
2. **Tab Navigation** — Switching between tabs
3. **List Interaction** — Tapping items in SwiftUI List
4. **Search Test** — Using system search field
5. **Error Validation** — Invalid input + error message check

For each scenario:
- Generates test code
- Shows what was found in RAG context
- Displays generated Swift code
- You manually verify if it looks correct

**Run with:** `python tests/validation/manual_validation.py`

---

## Expected Results

### ✅ Success Criteria
- All automated tests pass (8/8)
- Manual validation: 4/5 or 5/5 scenarios look correct
- Generated code compiles (manual Xcode check)
- Tests run on simulator (at least 3/5 execute)

### ❌ Red Flags
- Syntax errors in generated code
- RAG returns empty context
- Navigation service crashes
- Missing `waitForExistence` calls
- Wrong element queries (e.g., `app.tables` for SwiftUI List)

---

## Troubleshooting

### "Backend not reachable"
```bash
cd backend
uvicorn app.main:app --reload
```

### "RAG store is empty"
```bash
python -m rag.cli ingest \
  --app-dir /path/to/your/ios/app \
  --persist ./rag_store \
  --collection ios_app
```

### "Missing PROJECT_ROOT"
Add to `.env`:
```
PROJECT_ROOT=/path/to/your/ios/app
```

### Tests fail with "no module named requests"
```bash
pip install requests pytest
```

---

## Manual Xcode Validation (Optional)

After automated tests pass, manually test in Xcode:

1. Generate a test via the Streamlit UI or API
2. Copy the generated Swift code
3. Paste into `SampleAppUITests/LLMGeneratedTest.swift`
4. Build for testing: `⌘⇧U`
5. Run test: `⌘U`
6. Watch the simulator + check video recording

**Expected:** Test compiles, runs, and either passes or has a clear failure reason

---

## Next Steps

### If All Tests Pass:
1. Commit validation tests to branch
2. Merge `validation-tests` → `main`
3. Tag release: `git tag v2.0.0-pilot`
4. Start pilot outreach

### If Tests Fail:
1. Fix issues on `validation-tests` branch
2. Re-run validation
3. Iterate until green
4. Then merge to `main`

---

## Files

```
tests/validation/
├── README.md                   ← You are here
├── VALIDATION_PLAN.md          ← Full test plan document
├── test_end_to_end.py          ← Automated pytest tests
├── manual_validation.py        ← Interactive validation script
└── __init__.py                 ← Makes this a package
```
