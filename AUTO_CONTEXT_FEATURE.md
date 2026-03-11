# Auto Context Generation Feature

**Branch:** `feature/auto-context-generation`

---

## 🎯 **What This Does**

Automatically generates `APP_CONTEXT.md` from your indexed codebase whenever you run RAG indexing. This context is used to improve test enrichment quality.

**Problem Solved:**
- Manual app documentation is tedious
- Context gets out of sync with code
- Enrichment lacks app-specific knowledge

**Solution:**
- Extract context from RAG index automatically
- Always in sync with codebase
- Better, more specific test descriptions

---

## ✨ **Features**

### **1. Auto-Context Generation During Indexing**

When you index your code, APP_CONTEXT.md is automatically created/updated:

```bash
python -m rag.cli ingest \
  --app-dir /path/to/your/app \
  --persist ./rag_store \
  --collection ios_app \
  --auto-context  # DEFAULT: enabled
```

**What gets extracted:**
- ✅ Screen/View names
- ✅ Navigation patterns (TabView, NavigationLink, sheets)
- ✅ Entry screen detection
- ✅ Accessibility identifiers
- ✅ Common UI elements

### **2. LLM-as-Judge Quality Testing**

Automatically tests if context improves enrichment quality:

```bash
pytest tests/test_context_enrichment_quality.py -v
```

**What it tests:**
- ✅ Enrichment quality with vs without context
- ✅ Context adds screen names
- ✅ Context adds test credentials
- ✅ Context includes navigation flows
- ✅ Specificity, completeness, actionability scores

### **3. Enrichment Service Integration**

EnrichmentService automatically loads APP_CONTEXT.md:

```python
# Loads APP_CONTEXT.md if it exists
service = EnrichmentService(llm)

# Context is injected into enrichment prompts
result = service.enrich("test login")
# → Detailed, app-specific test description
```

---

## 🚀 **How to Use**

### **Step 1: Index Your Code (with auto-context)**

```bash
cd ios-test-automator-v2

# Index and auto-generate context (default behavior)
python -m rag.cli ingest \
  --app-dir /path/to/YourApp \
  --persist ./rag_store \
  --collection ios_app
```

**Output:**
```json
{
  "status": "ok",
  "indexed_swift_files": 42,
  "documents_upserted": 178,
  "context_generated": true
}
```

**Result:** `APP_CONTEXT.md` created automatically!

### **Step 2: Review Generated Context**

```bash
cat APP_CONTEXT.md
```

You'll see:
- Detected screens
- Navigation patterns
- Accessibility IDs
- Auto-generated timestamp

### **Step 3: Edit with Specifics (Optional)**

Add details the LLM can't extract from code:

```bash
nano APP_CONTEXT.md
```

Add:
- Test credentials (test@example.com / password123)
- Expected behaviors
- Business logic notes

### **Step 4: Restart Backend**

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

EnrichmentService automatically loads the new context!

---

## 🧪 **Running Tests**

### **LLM-as-Judge Quality Test**

```bash
# Run full test suite
pytest tests/test_context_enrichment_quality.py -v -s

# Run specific test
pytest tests/test_context_enrichment_quality.py::TestEnrichmentQuality::test_context_improves_enrichment -v -s
```

**What you'll see:**
```
Test Description: test login
============================================================

Without Context:
  Enriched: Launch the application and verify the login screen appears. Enter credentials...
  Score: 6/10
  Reasoning: Generic description, no specific screen names

With Context:
  Enriched: Launch the application and verify LoginView appears. Enter test@example.com and password123. Tap loginButton and verify navigation to ItemListView...
  Score: 9/10
  Reasoning: Specific screen names, includes credentials, detailed flow

PASSED ✅
```

### **Context Extraction Tests**

```bash
pytest tests/test_context_enrichment_quality.py::TestContextExtraction -v
```

Tests:
- ✅ Screen extraction
- ✅ Navigation pattern detection
- ✅ UI element extraction
- ✅ Document generation

---

## 📊 **Expected Improvements**

### **Before (No Context):**
```
Input: "test login"
Enriched: "Enter credentials and tap login button"
Quality Score: 5/10
```

### **After (With Context):**
```
Input: "test login"
Enriched: "Launch app and verify LoginView appears. Enter test@example.com 
          in emailTextField and password123 in passwordTextField. Tap 
          loginButton and verify navigation to ItemListView with first item visible."
Quality Score: 9/10
```

**Metrics:**
- **Specificity:** 4 → 9 (mentions LoginView, ItemListView, specific IDs)
- **Completeness:** 5 → 8 (includes setup, action, verification)
- **Context Awareness:** 3 → 9 (understands app structure)

---

## 🔧 **Configuration**

### **Disable Auto-Context**

```bash
python -m rag.cli ingest \
  --app-dir /path/to/app \
  --persist ./rag_store \
  --no-auto-context  # Skip context generation
```

### **Manual Context Generation**

```bash
# Generate context anytime
python3 generate_app_context.py
```

### **Custom Context Path**

```python
# In code
service = EnrichmentService(llm, app_context_path="/custom/path.md")
```

---

## 📁 **Files Changed**

```
backend/app/services/context_extractor.py    (NEW) - Extract context from RAG
backend/app/services/enrichment_service.py   (MOD) - Load context automatically
rag/cli.py                                   (MOD) - Add --auto-context flag
tests/test_context_enrichment_quality.py     (NEW) - LLM-as-judge tests
generate_app_context.py                      (NEW) - Manual generation script
APP_CONTEXT.md                               (MOD) - Updated template
```

---

## 🎯 **Integration Points**

1. **RAG Indexing** → Auto-generates context
2. **EnrichmentService** → Auto-loads context
3. **Test Generation** → Uses enriched descriptions
4. **Quality Assurance** → LLM-as-judge validates improvement

---

## 🔄 **Workflow**

```
1. Developer makes code changes
2. Run: python -m rag.cli ingest (with --auto-context)
3. APP_CONTEXT.md updated automatically
4. Backend reloads context on next start
5. Better test enrichment immediately
```

---

## ✅ **Success Criteria**

- ✅ Context auto-generates during indexing
- ✅ LLM-as-judge tests pass
- ✅ Quality scores improve with context
- ✅ Screen names appear in enrichments
- ✅ Navigation flows included
- ✅ No manual documentation needed

---

## 🚀 **Next Steps**

1. **Merge this branch** after tests pass
2. **Update pilot docs** with auto-context feature
3. **Add to CI/CD** to regenerate on code changes
4. **Monitor quality metrics** in production

---

**This feature makes test generation smarter without extra work!** 🎉
