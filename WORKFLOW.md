# Testara Agent Workflow

When Mher asks to implement, change, fix, or add anything to testara — run this workflow automatically. No need to ask.

## Trigger

Any actionable request about testara (new feature, refactor, bug fix, schema change, new endpoint, etc.)

---

## Pipeline: Planner → Builder → Reviewer

### Agent 1: Planner
**Role:** Analyze the request against the codebase, produce a precise implementation spec.

**Reads:**
- `backend/app/` structure
- Relevant files (config.py, prompts.py, test_runner.py, test_generator.py, schemas, validators, routes)
- Current git branch + recent commits

**Produces:** `swarm/artifacts/research/<TASK-ID>-spec.md`

Spec must include:
- Problem statement
- Files to change (list each one with what changes and why)
- New fields/functions/classes
- Removed fields/functions
- API contract changes
- Edge cases / risks
- Implementation order (dependencies first)

---

### Agent 2: Builder
**Role:** Implement the spec exactly. Create branch, write code, run syntax checks.

**Reads:** Planner spec from `swarm/artifacts/research/<TASK-ID>-spec.md`

**Does:**
- Creates a new git branch (`feature/<task-slug>`)
- Implements all changes in the spec
- Runs `python -m py_compile` on all modified files
- Greps for broken references after changes
- Stages all changes (`git add -A`)

**Produces:** Working code on branch + `swarm/artifacts/code/<TASK-ID>/summary.md`

---

### Agent 3: Reviewer
**Role:** QA + code review. Verify correctness, flag issues, give go/no-go.

**Reads:**
- Planner spec
- All modified files
- py_compile output

**Checks:**
- Does implementation match the spec?
- Any missing edge cases?
- Broken imports, stale references?
- API contract correctness?
- Are the flagged risk items addressed?

**Produces:** `swarm/artifacts/qa/<TASK-ID>-review.md`

Format:
```
## QA Report: <TASK-ID>

### ✅ Passing
- ...

### ⚠️ Issues
- [critical/major/minor] description

### Verdict: PASS | FAIL | NEEDS_REVISION
```

If PASS → I commit and push.
If NEEDS_REVISION → I send feedback to Builder, re-run.
If FAIL → I flag to Mher before committing.

---

## Orchestration (how I run this)

```
1. I announce: "Starting testara workflow for: <task>"
2. Spawn Planner subagent → wait for spec
3. Spawn Builder subagent with spec reference → wait for completion
4. Spawn Reviewer subagent → wait for QA report
5. If PASS: git commit + git push, report to Mher
6. If NEEDS_REVISION: loop Builder → Reviewer (max 2 retries)
7. If FAIL: report issues to Mher, don't commit
```

---

## Codebase Quick Reference (for agent prompts)

**Stack:** FastAPI + Python 3.11 + Appium-Python-Client + LangChain/Claude

**Key files:**
```
backend/app/
├── core/
│   ├── config.py          ← Settings (bundle_id, appium_*, rag_*, llm_*)
│   └── prompts.py         ← LLM system prompts
├── services/
│   ├── test_runner.py     ← AppiumTestRunner (subprocess harness)
│   ├── test_generator.py  ← TestGenerator (LLM → Python test fn)
│   ├── enrichment_service.py
│   └── rag_service.py
├── schemas/
│   └── test_schemas.py    ← Pydantic models (TestGenerationResponse has test_code)
├── utils/
│   └── validators.py      ← validate_appium_contract(), build_context_section()
├── api/routes/
│   ├── execution.py       ← POST /run-test
│   └── tests.py           ← POST /generate-test-with-rag
└── main.py                ← FastAPI lifespan, AppiumTestRunner init
```

**Current branch:** feature/appium-runner (Appium migration complete)
**Main branch:** main

**Conventions:**
- New fields in config.py → also add to .env example
- Schema changes → update both request and response models
- Always run py_compile after changes
- Grep for broken refs: `grep -r "old_symbol" backend/app/`
