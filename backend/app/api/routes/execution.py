"""Test execution routes — Appium runner."""
import asyncio
import logging
import uuid
from typing import List, Optional
import json as _json

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.prompts import RETRY_CONTEXT_TEMPLATE
from app.schemas.test_schemas import AppContext, TestGenerationRequest

logger = logging.getLogger(__name__)
router = APIRouter()


class TestExecutionRequest(BaseModel):
    test_code: str
    bundle_id: Optional[str] = None
    device_udid: str = ""
    record_video: bool = False


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

        return TestExecutionResponse(
            success=result.get("success", False),
            test_id=result.get("test_id", ""),
            video_url=video_url,
            logs=result.get("logs", ""),
            duration=result.get("duration", 0.0),
            error=result.get("error"),
            screenshot=result.get("screenshot"),
        )

    except Exception as e:
        logger.error("Test execution failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Auto-retry helpers
# ---------------------------------------------------------------------------

def _is_retriable_error(exec_result: dict) -> bool:
    """Return True only if the failure is a test execution error (not an assertion failure).

    Exit code semantics from harness:
      0 → success
      1 → AssertionError (test ran correctly, assertion was wrong) — DO NOT retry
      2 → other exception (Appium error, timeout, etc.)           — DO retry
    """
    if exec_result.get("success"):
        return False
    error = exec_result.get("error", "")
    # AssertionError = test ran correctly but found wrong value — don't retry
    if error.startswith("Assertion failed:"):
        return False
    # Any other error = Appium error, timeout, element not found — retry
    return True


# ---------------------------------------------------------------------------
# Auto-retry: generate + run in a loop
# ---------------------------------------------------------------------------

class AttemptSummary(BaseModel):
    attempt: int
    test_code: str
    success: bool
    error: Optional[str] = None
    duration: float = 0.0


class GenerateAndRunRequest(BaseModel):
    test_description: str
    bundle_id: Optional[str] = None
    device_udid: str = ""
    max_attempts: Optional[int] = None
    record_video: bool = False
    rag_top_k: Optional[int] = None
    app_name: Optional[str] = None


class GenerateAndRunResponse(BaseModel):
    success: bool
    attempts: int
    test_id: str
    test_code: str
    logs: str = ""
    duration: float = 0.0
    video_url: Optional[str] = None
    error: Optional[str] = None
    screenshot: Optional[str] = None
    history: List[AttemptSummary] = Field(default_factory=list)


@router.post("/generate-and-run", response_model=GenerateAndRunResponse)
async def generate_and_run(request: Request, body: GenerateAndRunRequest):
    """Generate a test and run it, retrying with error context on failure.
    
    Only retries on execution errors (exit code 2).
    Does NOT retry on assertion failures (exit code 1) — those are valid test results.
    """
    generator = request.app.state.test_generator
    test_runner = request.app.state.test_runner
    rag_service = request.app.state.rag_service
    enrichment_service = request.app.state.enrichment_service

    if test_runner is None:
        raise HTTPException(
            status_code=503,
            detail="Appium test runner not available. Is the Appium server running?",
        )

    max_attempts = min(body.max_attempts or settings.auto_retry_max_attempts, 5)
    effective_bundle_id = body.bundle_id or settings.bundle_id
    resolved_app_name = body.app_name or settings.default_app_name

    # --- Enrich + RAG once (reused across all retry attempts) ---
    try:
        enrichment = await asyncio.to_thread(enrichment_service.enrich, body.test_description)
        enriched_description = enrichment.get("enriched", body.test_description)
    except Exception as e:
        logger.warning("Enrichment failed, using original description: %s", e)
        enriched_description = body.test_description

    try:
        rag_context = rag_service.query(enriched_description, k=body.rag_top_k)
    except Exception as e:
        logger.warning("RAG query failed, proceeding without RAG context: %s", e)
        rag_context = {"screens": [], "accessibility_ids": [], "code_snippets": []}

    code_snippets_text = "\n\n".join(
        f"// {s['kind']} from {s['path']}\n{s['content']}"
        for s in rag_context.get("code_snippets", [])
    )

    app_context = AppContext(
        app_name=resolved_app_name,
        screens=rag_context.get("screens", []),
        accessibility_ids=rag_context.get("accessibility_ids", []),
        source_code_snippets=code_snippets_text or None,
    )

    # --- Retry loop ---
    retry_context: Optional[str] = None
    last_result: Optional[dict] = None
    last_test_code: str = ""
    history: List[AttemptSummary] = []

    for attempt in range(1, max_attempts + 1):
        logger.info("Attempt %d/%d: generating test...", attempt, max_attempts)

        gen_request = TestGenerationRequest(
            test_description=enriched_description,
            test_type="ui",
            app_context=app_context,
            include_comments=True,
        )

        try:
            gen_response = await asyncio.to_thread(
                generator.run, gen_request, None, retry_context
            )
            test_code = gen_response.test_code
            last_test_code = test_code
        except Exception as e:
            logger.error("Attempt %d/%d: generation failed: %s", attempt, max_attempts, e)
            raise HTTPException(status_code=500, detail=f"Test generation failed: {e}")

        logger.info("Attempt %d/%d: running test...", attempt, max_attempts)
        try:
            result = await test_runner.run_test(
                test_code=test_code,
                bundle_id=effective_bundle_id,
                device_udid=body.device_udid,
                record_video=body.record_video,
            )
            last_result = result
        except Exception as e:
            logger.error("Attempt %d/%d: runner raised exception: %s", attempt, max_attempts, e)
            last_result = {
                "success": False,
                "error": str(e),
                "logs": "",
                "test_id": str(uuid.uuid4()),
                "duration": 0.0,
            }

        history.append(AttemptSummary(
            attempt=attempt,
            test_code=test_code,
            success=last_result.get("success", False),
            error=last_result.get("error"),
            duration=last_result.get("duration", 0.0),
        ))

        if last_result.get("success"):
            logger.info("Attempt %d/%d: PASSED", attempt, max_attempts)
            video_url = None
            if last_result.get("video_path"):
                video_url = f"/recordings/{last_result['video_path']}"
            return GenerateAndRunResponse(
                success=True,
                attempts=attempt,
                test_id=last_result.get("test_id", str(uuid.uuid4())),
                test_code=test_code,
                logs=last_result.get("logs", ""),
                duration=last_result.get("duration", 0.0),
                video_url=video_url,
                error=None,
                screenshot=last_result.get("screenshot"),
                history=history,
            )

        # Check if the failure is worth retrying
        if not _is_retriable_error(last_result):
            logger.info(
                "Attempt %d/%d: assertion failure — not retrying: %s",
                attempt, max_attempts, last_result.get("error"),
            )
            break  # exit retry loop — return result as-is below

        logger.info("Attempt %d/%d: execution error — retrying...", attempt, max_attempts)
        retry_context = RETRY_CONTEXT_TEMPLATE.format(
            attempt=attempt,
            max_attempts=max_attempts,
            error=last_result.get("error", "Unknown error"),
            logs=last_result.get("logs", "")[-2000:],
            previous_code=test_code,
        )

    # All attempts exhausted (or assertion failure broke the loop)
    logger.warning("Returning failure after %d attempt(s).", len(history))
    video_url = None
    if last_result and last_result.get("video_path"):
        video_url = f"/recordings/{last_result['video_path']}"
    return GenerateAndRunResponse(
        success=False,
        attempts=len(history),
        test_id=last_result.get("test_id", str(uuid.uuid4())) if last_result else str(uuid.uuid4()),
        test_code=last_test_code,
        logs=last_result.get("logs", "") if last_result else "",
        duration=last_result.get("duration", 0.0) if last_result else 0.0,
        video_url=video_url,
        error=last_result.get("error") if last_result else "All attempts failed",
        screenshot=last_result.get("screenshot") if last_result else None,
        history=history,
    )


# ---------------------------------------------------------------------------
# SSE streaming endpoint
# ---------------------------------------------------------------------------

@router.get("/generate-and-run/stream")
async def generate_and_run_stream(
    request: Request,
    test_description: str,
    bundle_id: str = "",
    device_udid: str = "",
    max_attempts: int = 3,
    record_video: bool = False,
    app_name: str = "",
):
    """SSE endpoint — streams progress events for each attempt.

    Event types:
      status           {"message": str}
      attempt_start    {"attempt": int, "max": int}
      generating       {"attempt": int}
      generated        {"attempt": int, "test_code": str}
      running          {"attempt": int}
      success          {"attempt", "test_id", "test_code", "logs", "duration", "history"}
      assertion_failure{"attempt", "error", "logs", "test_code", "history"}
      error_retry      {"attempt", "error", "next_attempt"}
      exhausted        {"attempts", "error", "test_code", "history"}
      fatal_error      {"error": str}
    """

    async def event_stream():
        generator = request.app.state.test_generator
        test_runner = request.app.state.test_runner
        rag_service = request.app.state.rag_service
        enrichment_service = request.app.state.enrichment_service

        effective_bundle_id = bundle_id or settings.bundle_id
        effective_max = min(max_attempts, 5)
        history = []
        retry_context = None

        def send(event_type: str, data: dict) -> str:
            return f"data: {_json.dumps({'type': event_type, **data})}\n\n"

        try:
            # --- Enrich + RAG once ---
            yield send("status", {"message": "Enriching description..."})
            try:
                enrichment = await asyncio.to_thread(enrichment_service.enrich, test_description)
                enriched = enrichment.get("enriched", test_description)
            except Exception as e:
                logger.warning("Enrichment failed in SSE stream: %s", e)
                enriched = test_description

            yield send("status", {"message": "Retrieving context..."})
            try:
                rag_context = rag_service.query(enriched)
            except Exception as e:
                logger.warning("RAG query failed in SSE stream: %s", e)
                rag_context = {"screens": [], "accessibility_ids": [], "code_snippets": []}

            resolved_app_name = app_name or settings.default_app_name
            app_context = AppContext(
                app_name=resolved_app_name,
                screens=rag_context.get("screens", []),
                accessibility_ids=rag_context.get("accessibility_ids", []),
                source_code_snippets="\n\n".join(
                    f"// {s['kind']} from {s['path']}\n{s['content']}"
                    for s in rag_context.get("code_snippets", [])
                ) or None,
            )

            exec_result: dict = {}
            test_code: str = ""

            for attempt in range(1, effective_max + 1):
                yield send("attempt_start", {"attempt": attempt, "max": effective_max})

                # Generate
                yield send("generating", {"attempt": attempt})
                gen_request = TestGenerationRequest(
                    test_description=enriched,
                    test_type="ui",
                    app_context=app_context,
                    include_comments=True,
                )
                try:
                    test_response = await asyncio.to_thread(
                        generator.run, gen_request, None, retry_context
                    )
                    test_code = test_response.test_code
                except Exception as e:
                    yield send("fatal_error", {"error": f"Generation failed: {e}"})
                    return

                yield send("generated", {"attempt": attempt, "test_code": test_code})

                # Run
                yield send("running", {"attempt": attempt})
                try:
                    exec_result = await test_runner.run_test(
                        test_code=test_code,
                        bundle_id=effective_bundle_id,
                        device_udid=device_udid,
                        record_video=record_video,
                    )
                except Exception as e:
                    exec_result = {
                        "success": False,
                        "error": str(e),
                        "logs": "",
                        "test_id": str(uuid.uuid4()),
                        "duration": 0.0,
                    }

                history.append({
                    "attempt": attempt,
                    "test_code": test_code,
                    "success": exec_result.get("success", False),
                    "error": exec_result.get("error"),
                    "duration": exec_result.get("duration", 0.0),
                })

                if exec_result.get("success"):
                    yield send("success", {
                        "attempt": attempt,
                        "test_id": exec_result.get("test_id", ""),
                        "test_code": test_code,
                        "logs": exec_result.get("logs", ""),
                        "duration": exec_result.get("duration", 0.0),
                        "history": history,
                    })
                    return

                # Check retriability
                error = exec_result.get("error", "")
                is_retriable = _is_retriable_error(exec_result)

                if not is_retriable:
                    yield send("assertion_failure", {
                        "attempt": attempt,
                        "error": error,
                        "logs": exec_result.get("logs", ""),
                        "test_code": test_code,
                        "history": history,
                    })
                    return

                yield send("error_retry", {
                    "attempt": attempt,
                    "error": error,
                    "next_attempt": attempt + 1 if attempt < effective_max else None,
                })

                retry_context = RETRY_CONTEXT_TEMPLATE.format(
                    attempt=attempt,
                    max_attempts=effective_max,
                    error=error,
                    logs=exec_result.get("logs", "")[-2000:],
                    previous_code=test_code,
                )

            # All attempts exhausted
            yield send("exhausted", {
                "attempts": effective_max,
                "error": exec_result.get("error"),
                "test_code": test_code,
                "history": history,
            })

        except Exception as e:
            logger.error("SSE stream fatal error: %s", e, exc_info=True)
            yield send("fatal_error", {"error": str(e)})

    return StreamingResponse(event_stream(), media_type="text/event-stream")
