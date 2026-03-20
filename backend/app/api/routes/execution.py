"""Test execution routes — Appium runner."""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.core.config import settings

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
