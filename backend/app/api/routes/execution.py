"""Test execution routes"""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()


class TestExecutionRequest(BaseModel):
    test_code: str
    app_name: str = "YourApp"
    device: str = "iPhone 15 Pro"
    ios_version: str = "17.0"


class TestExecutionResponse(BaseModel):
    success: bool
    test_id: str
    video_url: Optional[str] = None
    logs: str = ""
    duration: float = 0.0
    device: str = ""
    ios_version: str = ""
    error: Optional[str] = None


@router.post("/run-test", response_model=TestExecutionResponse)
async def run_test(request: Request, body: TestExecutionRequest):
    """
    Run a test in iOS Simulator and record video.
    
    Returns video URL, test results, and execution logs.
    """
    test_runner = request.app.state.test_runner
    lock = request.app.state.test_execution_lock

    try:
        async with lock:
            logger.info("Test execution lock acquired — Appium discovery blocked until test completes")
            result = await test_runner.run_test(
                test_code=body.test_code,
                app_name=body.app_name,
                device=body.device,
                ios_version=body.ios_version
            )
        logger.info("Test execution lock released")
        
        # Build video URL if recording succeeded
        video_url = None
        if result.get("video_path"):
            video_url = f"/recordings/{result['video_path']}"
        
        return TestExecutionResponse(
            success=result.get("success", False),
            test_id=result.get("test_id", ""),
            video_url=video_url,
            logs=result.get("logs", ""),
            duration=result.get("duration", 0.0),
            device=result.get("device", body.device),
            ios_version=result.get("ios_version", body.ios_version),
            error=result.get("error")
        )
        
    except Exception as e:
        logger.error(f"Test execution failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
