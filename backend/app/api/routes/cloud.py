"""Cloud execution routes — BrowserStack App Automate integration."""
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.browserstack_service import BrowserStackService, DEFAULT_DEVICES, get_browserstack_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/cloud", tags=["cloud"])


# ── Request / Response models ─────────────────────────────────────────────────

class CloudStatusResponse(BaseModel):
    enabled: bool
    provider: Optional[str] = None
    credentials_valid: Optional[bool] = None
    app_url: Optional[str] = None
    default_device: Optional[str] = None
    os_version: Optional[str] = None


class AppUploadRequest(BaseModel):
    ipa_path: str
    custom_id: Optional[str] = "testara-app"


class AppUploadResponse(BaseModel):
    app_url: str
    message: str


class DeviceListResponse(BaseModel):
    devices: List[Dict[str, Any]]
    total: int


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/status", response_model=CloudStatusResponse)
async def cloud_status():
    """
    Return current cloud execution status.
    Shows whether BrowserStack is configured and credentials are valid.
    """
    from app.core.config import settings

    bs = get_browserstack_service()
    if not bs:
        return CloudStatusResponse(enabled=False)

    credentials_valid = await bs.validate_credentials()
    return CloudStatusResponse(
        enabled=True,
        provider="browserstack",
        credentials_valid=credentials_valid,
        app_url=settings.browserstack_app_url or None,
        default_device=settings.browserstack_device,
        os_version=settings.browserstack_os_version,
    )


@router.post("/upload", response_model=AppUploadResponse)
async def upload_app(req: AppUploadRequest):
    """
    Upload an .ipa file to BrowserStack and return the bs:// app URL.
    Store the returned app_url as BROWSERSTACK_APP_URL in .env to avoid
    re-uploading on every cloud run.
    """
    bs = get_browserstack_service()
    if not bs:
        raise HTTPException(
            status_code=400,
            detail="BrowserStack is not configured. Set BROWSERSTACK_USERNAME and BROWSERSTACK_ACCESS_KEY in .env",
        )

    try:
        app_url = await bs.upload_app(req.ipa_path, custom_id=req.custom_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    return AppUploadResponse(
        app_url=app_url,
        message=f"App uploaded successfully. Set BROWSERSTACK_APP_URL={app_url} in .env to reuse.",
    )


@router.get("/devices", response_model=DeviceListResponse)
async def list_devices():
    """
    List available iOS devices on BrowserStack.
    Returns the full device list plus a set of recommended presets.
    """
    bs = get_browserstack_service()
    if not bs:
        raise HTTPException(
            status_code=400,
            detail="BrowserStack is not configured.",
        )

    try:
        devices = await bs.list_ios_devices()
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    return DeviceListResponse(devices=devices, total=len(devices))


@router.get("/devices/recommended")
async def recommended_devices():
    """Return the built-in list of recommended iOS device presets."""
    return {"devices": DEFAULT_DEVICES}
