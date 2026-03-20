"""Test execution routes — Appium runner."""
import asyncio
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.core.config import settings
from app.schemas.test_schemas import AppContext, TestGenerationRequest, RAGTestGenerationRequest

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


class GenerateAndRunRequest(BaseModel):
    test_description: str
    bundle_id: Optional[str] = None
    device_udid: str = ""
    record_video: bool = False


class GenerateAndRunResponse(BaseModel):
    success: bool
    test_id: str
    test_code: str
    attempts: int
    logs: str = ""
    duration: float = 0.0
    error: Optional[str] = None


@router.post("/generate-and-run", response_model=GenerateAndRunResponse)
async def generate_and_run(request: Request, body: GenerateAndRunRequest):
    """Generate a test, run it. If it errors, feed the error back to the LLM, regenerate, and run once more."""
    generator = request.app.state.test_generator
    test_runner = request.app.state.test_runner
    rag_service = request.app.state.rag_service
    enrichment_service = request.app.state.enrichment_service

    if test_runner is None:
        raise HTTPException(status_code=503, detail="Appium test runner not available.")

    effective_bundle_id = body.bundle_id or settings.bundle_id

    try:
        # Enrich + RAG once
        enrichment = await asyncio.to_thread(enrichment_service.enrich, body.test_description)
        enriched = enrichment["enriched"]
        rag_context = rag_service.query(enriched)

        code_snippets = "\n\n".join(
            f"// {s['kind']} from {s['path']}\n{s['content']}"
            for s in rag_context.get("code_snippets", [])
        )
        app_context = AppContext(
            app_name=settings.default_app_name,
            screens=rag_context.get("screens", []),
            accessibility_ids=rag_context.get("accessibility_ids", []),
            source_code_snippets=code_snippets or None,
        )
        gen_request = TestGenerationRequest(
            test_description=enriched,
            test_type="ui",
            app_context=app_context,
            include_comments=True,
        )

        # Attempt 1
        logger.info("generate-and-run: attempt 1")
        test_response = await asyncio.to_thread(generator.run, gen_request)
        result = await test_runner.run_test(
            test_code=test_response.test_code,
            bundle_id=effective_bundle_id,
            device_udid=body.device_udid,
            record_video=body.record_video,
        )

        # If execution error (not assertion failure) → regenerate with error, run once more
        error = result.get("error", "")
        if not result.get("success") and not error.startswith("Assertion failed:"):
            logger.info("generate-and-run: attempt 1 errored, regenerating with error context")
            test_response = await asyncio.to_thread(generator.run, gen_request, None, error)
            result = await test_runner.run_test(
                test_code=test_response.test_code,
                bundle_id=effective_bundle_id,
                device_udid=body.device_udid,
                record_video=body.record_video,
            )
            attempts = 2
        else:
            attempts = 1

        return GenerateAndRunResponse(
            success=result.get("success", False),
            test_id=result.get("test_id", ""),
            test_code=test_response.test_code,
            attempts=attempts,
            logs=result.get("logs", ""),
            duration=result.get("duration", 0.0),
            error=result.get("error"),
        )

    except Exception as e:
        logger.error("generate-and-run failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


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

        # If it errored (not an assertion failure), retry once automatically
        if not result.get("success") and not (result.get("error") or "").startswith("Assertion failed:"):
            logger.info("Test errored on attempt 1, retrying once: %s", result.get("error"))
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

        return TestExecutionResponse(
            success=result.get("success", False),
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
