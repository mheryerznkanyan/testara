"""Test execution routes — Appium runner."""
import asyncio
import logging
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.core.config import settings

try:
    from langsmith import Client as LangSmithClient
    _LANGSMITH_AVAILABLE = True
except ImportError:
    _LANGSMITH_AVAILABLE = False

logger = logging.getLogger(__name__)
router = APIRouter()


class TestExecutionRequest(BaseModel):
    test_code: str
    bundle_id: Optional[str] = None
    device_udid: str = ""
    record_video: bool = False
    langsmith_run_id: Optional[str] = None


class TestExecutionResponse(BaseModel):
    success: bool
    test_id: str
    video_url: Optional[str] = None
    logs: str = ""
    duration: float = 0.0
    error: Optional[str] = None
    screenshot: Optional[str] = None


@router.post("/run-test", response_model=TestExecutionResponse)
async def run_test(request: Request, body: TestExecutionRequest):
    """Run a generated Python Appium test on a simulator."""
    test_runner = request.app.state.test_runner

    if test_runner is None:
        raise HTTPException(
            status_code=503,
            detail="Appium test runner not available. Is the Appium server running?",
        )

    effective_bundle_id = body.bundle_id or settings.bundle_id

    try:
        result = await test_runner.run_test(
            test_code=body.test_code,
            bundle_id=effective_bundle_id,
            device_udid=body.device_udid,
            record_video=body.record_video,
        )

        video_url = None
        if result.get("video_path"):
            video_url = f"/recordings/{result['video_path']}"

        screenshot_url = None
        if result.get("screenshot"):
            screenshot_url = f"/recordings/{result['screenshot']}"

        success = result.get("success", False)

        # Send feedback + save to dataset in LangSmith
        if (
            _LANGSMITH_AVAILABLE
            and settings.langsmith_tracing
            and settings.langsmith_api_key
        ):
            try:
                client = LangSmithClient()

                # Feedback linked to generation run
                if body.langsmith_run_id:
                    client.create_feedback(
                        run_id=body.langsmith_run_id,
                        key="test_result",
                        score=1.0 if success else 0.0,
                        comment=result.get("error") or ("Test passed" if success else "Test failed"),
                        feedback_source_type="api",
                    )

                # Save to Testara dataset with trace linked
                example_data = {
                    "inputs": {"test_code": body.test_code},
                    "outputs": {
                        "passed": success,
                        "duration": result.get("duration", 0),
                        "error": result.get("error"),
                        "test_id": result.get("test_id", ""),
                    },
                }
                if body.langsmith_run_id:
                    example_data["source_run_id"] = body.langsmith_run_id
                client.create_examples(
                    dataset_name="Testara",
                    examples=[example_data],
                )
                logger.info("LangSmith: feedback + dataset example saved")
            except Exception as e:
                logger.warning("Failed to send LangSmith data: %s", e)

        return TestExecutionResponse(
            success=success,
            test_id=result.get("test_id", ""),
            video_url=video_url,
            logs=result.get("logs", ""),
            duration=result.get("duration", 0.0),
            error=result.get("error"),
            screenshot=screenshot_url,
        )

    except Exception as e:
        logger.error("Test execution failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Test Suite: auto-generate + batch run
# ---------------------------------------------------------------------------

class TestSuiteRequest(BaseModel):
    count: int = 25
    bundle_id: Optional[str] = None
    device_udid: str = ""


class TestSuiteResult(BaseModel):
    description: str
    test_code: str
    success: bool
    duration: float = 0.0
    error: Optional[str] = None


class TestSuiteResponse(BaseModel):
    total: int
    passed: int
    failed: int
    results: List[TestSuiteResult]


@router.post("/run-test-suite", response_model=TestSuiteResponse)
async def run_test_suite(request: Request, body: TestSuiteRequest):
    """Auto-generate test descriptions from discovery, generate code, run all, report results."""
    from app.utils.accessibility_tree_parser import MultiScreenSnapshot
    from app.schemas.test_schemas import AppContext, TestGenerationRequest

    # 1. Load discovery snapshot
    snapshot_path = Path(settings.rag_persist_dir) / "discovery_snapshot.json"
    if not snapshot_path.exists():
        raise HTTPException(
            status_code=400,
            detail="No discovery snapshot found. Run /discover first to capture the app's screens.",
        )
    snapshot = MultiScreenSnapshot.load(str(snapshot_path))
    if not snapshot.screens:
        raise HTTPException(status_code=400, detail="Discovery snapshot has no screens.")

    # 2. Generate test descriptions from discovery
    suite_generator = getattr(request.app.state, "suite_generator", None)
    if suite_generator is None:
        raise HTTPException(status_code=503, detail="Suite generator not initialized.")

    descriptions = await asyncio.to_thread(
        suite_generator.generate_descriptions, snapshot, body.count
    )
    if not descriptions:
        raise HTTPException(status_code=500, detail="Failed to generate test descriptions.")

    logger.info("Suite: generated %d test descriptions", len(descriptions))

    # 3. Generate test code for each description (parallel)
    generator = request.app.state.test_generator
    rag_service = request.app.state.rag_service

    async def generate_one(desc: str):
        rag_context = await asyncio.to_thread(rag_service.query, desc)
        code_snippets_text = "\n\n".join(
            f"// {s['kind']} from {s['path']}\n{s['content']}"
            for s in rag_context.get("code_snippets", [])
        )
        app_context = AppContext(
            app_name=settings.default_app_name,
            screens=rag_context.get("screens", []),
            accessibility_ids=rag_context.get("accessibility_ids", []),
            source_code_snippets=code_snippets_text or None,
        )
        gen_request = TestGenerationRequest(
            test_description=desc,
            test_type="ui",
            app_context=app_context,
        )
        return await asyncio.to_thread(generator.run, gen_request, snapshot)

    # Generate sequentially with retry on rate limit
    gen_results = []
    for i, desc in enumerate(descriptions):
        logger.info("Suite: generating test %d/%d — %s", i + 1, len(descriptions), desc[:60])
        gen_result = None
        for attempt in range(3):
            try:
                gen_result = await generate_one(desc)
                break
            except Exception as e:
                if "429" in str(e) or "rate_limit" in str(e):
                    wait_time = 30 * (attempt + 1)
                    logger.warning("Rate limited on test %d, waiting %ds...", i + 1, wait_time)
                    await asyncio.sleep(wait_time)
                else:
                    gen_result = e
                    break
        gen_results.append(gen_result if gen_result is not None else Exception("All retries exhausted"))
        if i < len(descriptions) - 1:
            logger.info("Suite: waiting 60s before next generation (rate limit)...")
            await asyncio.sleep(60)

    # 4. Execute each test sequentially (Appium is single-session)
    test_runner = request.app.state.test_runner
    effective_bundle_id = body.bundle_id or settings.bundle_id
    results: List[TestSuiteResult] = []

    for i, (desc, gen) in enumerate(zip(descriptions, gen_results)):
        if isinstance(gen, Exception):
            logger.warning("Suite test %d generation failed: %s", i + 1, gen)
            results.append(TestSuiteResult(
                description=desc, test_code="", success=False,
                error=f"Generation failed: {gen}",
            ))
            continue

        logger.info("Suite: running test %d/%d — %s", i + 1, len(descriptions), desc[:60])

        try:
            exec_result = await test_runner.run_test(
                test_code=gen.test_code,
                bundle_id=effective_bundle_id,
                device_udid=body.device_udid,
            )

            # Send LangSmith feedback
            run_id = gen.metadata.get("langsmith_run_id")
            if (
                _LANGSMITH_AVAILABLE
                and settings.langsmith_tracing
                and settings.langsmith_api_key
                and run_id
            ):
                try:
                    client = LangSmithClient()
                    client.create_feedback(
                        run_id=run_id,
                        key="test_result",
                        score=1.0 if exec_result.get("success") else 0.0,
                        comment=exec_result.get("error") or "Test passed",
                        feedback_source_type="api",
                    )
                except Exception as e:
                    logger.warning("LangSmith feedback failed for test %d: %s", i + 1, e)

            results.append(TestSuiteResult(
                description=desc,
                test_code=gen.test_code,
                success=exec_result.get("success", False),
                duration=exec_result.get("duration", 0),
                error=exec_result.get("error"),
            ))

        except Exception as e:
            logger.error("Suite test %d execution failed: %s", i + 1, e)
            results.append(TestSuiteResult(
                description=desc, test_code=gen.test_code, success=False,
                error=str(e),
            ))

    passed = sum(1 for r in results if r.success)
    logger.info("Suite complete: %d/%d passed", passed, len(results))

    # Push results to LangSmith dataset
    dataset_name = None
    if (
        _LANGSMITH_AVAILABLE
        and settings.langsmith_tracing
        and settings.langsmith_api_key
        and results
    ):
        try:
            client = LangSmithClient()
            dataset_name = "Testara"
            examples = []
            for j, r in enumerate(results):
                ex = {
                    "inputs": {"test_description": r.description},
                    "outputs": {
                        "test_code": r.test_code,
                        "passed": r.success,
                        "duration": r.duration,
                        "error": r.error,
                    },
                }
                # Link the generation trace so the full pipeline is visible from the dataset
                gen = gen_results[j] if j < len(gen_results) else None
                if gen and not isinstance(gen, Exception):
                    run_id = gen.metadata.get("langsmith_run_id")
                    if run_id:
                        ex["source_run_id"] = run_id
                examples.append(ex)
            client.create_examples(dataset_name=dataset_name, examples=examples)
            logger.info("LangSmith dataset created: %s (%d examples)", dataset_name, len(examples))
        except Exception as e:
            logger.warning("Failed to create LangSmith dataset: %s", e)

    return TestSuiteResponse(
        total=len(results),
        passed=passed,
        failed=len(results) - passed,
        results=results,
    )
