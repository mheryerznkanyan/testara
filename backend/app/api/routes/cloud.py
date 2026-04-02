"""Cloud execution routes — Testara Cloud (powered by real device infrastructure)."""
import asyncio
import logging
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import httpx

from app.core.config import settings
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
async def upload_app(
    file: Optional[UploadFile] = File(None),
    req: Optional[AppUploadRequest] = None,
):
    """
    Upload an .ipa file and return an app URL.
    Accepts either:
      - A multipart file upload (file field)
      - A JSON body with ipa_path (local file path)

    If BrowserStack is configured the IPA is forwarded there and a bs:// URL
    is returned.  Otherwise the file is stored locally under uploads/ and a
    local file:// path is returned (self-hosted Mac mode).
    """
    ipa_path = None
    tmp_path = None

    try:
        if file and file.filename:
            suffix = Path(file.filename).suffix or ".ipa"
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            content = await file.read()
            tmp.write(content)
            tmp.close()
            ipa_path = tmp.name
            tmp_path = tmp.name
        elif req and req.ipa_path:
            ipa_path = req.ipa_path
        else:
            raise HTTPException(status_code=400, detail="Provide either a file upload or ipa_path")

        # ── Upload to Supabase Storage ────────────────────────────────────────
        from app.services.supabase_service import upload_app_to_storage
        original_name = Path(file.filename).name if file and file.filename else Path(ipa_path).name
        try:
            app_url = await asyncio.get_event_loop().run_in_executor(
                None, upload_app_to_storage, ipa_path, original_name
            )
        except RuntimeError as e:
            raise HTTPException(status_code=502, detail=str(e))
        message = f"App uploaded to Supabase Storage — {app_url}"

    finally:
        if tmp_path:
            try:
                Path(tmp_path).unlink(missing_ok=True)
            except Exception:
                pass

    return AppUploadResponse(app_url=app_url, message=message)


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


POPULAR_MODELS = {
    "iPhone 16 Pro Max", "iPhone 16 Pro", "iPhone 16",
    "iPhone 15 Pro Max", "iPhone 15 Pro", "iPhone 15",
    "iPhone 14 Pro", "iPhone 14",
    "iPhone 13",
    "iPhone SE 2022",
    "iPad Pro 12.9 2022", "iPad Air 5",
}


@router.get("/devices/recommended")
async def recommended_devices():
    """Return curated popular iOS devices from BrowserStack."""
    bs = get_browserstack_service()
    if not bs:
        return [{"name": d["device"], "os_version": d["os_version"]} for d in DEFAULT_DEVICES]

    try:
        all_devices = await bs.list_ios_devices()
        filtered = [
            {"name": d.get("device"), "os_version": d.get("os_version")}
            for d in all_devices
            if d.get("device") in POPULAR_MODELS
        ]
        # Deduplicate and sort by device name then os_version desc
        seen = set()
        unique = []
        for d in sorted(filtered, key=lambda x: (x["name"], x["os_version"]), reverse=True):
            key = f"{d['name']}_{d['os_version']}"
            if key not in seen:
                seen.add(key)
                unique.append(d)
        return unique[:20] if unique else [{"name": d["device"], "os_version": d["os_version"]} for d in DEFAULT_DEVICES]
    except Exception as e:
        logger.warning("Failed to fetch BS devices, using defaults: %s", e)
        return [{"name": d["device"], "os_version": d["os_version"]} for d in DEFAULT_DEVICES]


# ── Simulator Device List (self-hosted Mac) ───────────────────────────────────

@router.get("/devices/simulators")
async def list_simulators():
    """
    Fetch available iOS simulators from the self-hosted Mac device server.
    Requires DEVICE_SERVER_URL env var pointing to the Mac running device_server.py
    e.g. http://195.82.45.157:4724
    """
    device_server_url = settings.device_server_url
    if not device_server_url:
        raise HTTPException(
            status_code=503,
            detail="DEVICE_SERVER_URL is not configured. Run scripts/device_server.py on your Mac and set the env var.",
        )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{device_server_url.rstrip('/')}/devices")
            resp.raise_for_status()
            return resp.json()
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Device server timed out. Is device_server.py running on your Mac?")
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Could not reach device server: {e}")


# ── Cloud Discovery ────────────────────────────────────────────────────────────

class CloudDiscoveryRequest(BaseModel):
    app_url: Optional[str] = None
    device_name: Optional[str] = None
    os_version: Optional[str] = None


class ScreenDetail(BaseModel):
    name: str
    element_count: int
    navigation_path: str = ""


class CloudDiscoveryResponse(BaseModel):
    success: bool
    screen_count: int = 0
    interactive_count: int = 0
    screens: list[ScreenDetail] = []
    error: Optional[str] = None


@router.get("/discover/status", response_model=CloudDiscoveryResponse)
async def discovery_status():
    """Check if a cached discovery snapshot exists."""
    snapshot_path = Path(settings.rag_persist_dir) / "discovery_snapshot.json"
    if not snapshot_path.exists():
        return CloudDiscoveryResponse(success=False, error="No discovery snapshot cached")

    try:
        from app.utils.accessibility_tree_parser import MultiScreenSnapshot
        snapshot = MultiScreenSnapshot.load(str(snapshot_path))
        interactive_count = len(snapshot.all_interactive_elements())
        screen_details = [
            ScreenDetail(
                name=s.screen_label,
                element_count=len(s.interactive_elements()),
                navigation_path=s.navigation_path,
            )
            for s in snapshot.screens
        ]
        return CloudDiscoveryResponse(
            success=True,
            screen_count=len(snapshot.screens),
            interactive_count=interactive_count,
            screens=screen_details,
        )
    except Exception as e:
        return CloudDiscoveryResponse(success=False, error=str(e))


@router.post("/discover", response_model=CloudDiscoveryResponse)
async def cloud_discover(body: CloudDiscoveryRequest):
    """
    Discover app accessibility tree on a real BrowserStack device.

    Launches the app, navigates screens, captures the accessibility tree,
    and caches it for test generation. Takes 30-90 seconds.
    """
    bs = get_browserstack_service()
    if not bs:
        raise HTTPException(status_code=400, detail="Cloud infrastructure is not configured.")

    app_url = body.app_url or settings.browserstack_app_url
    if not app_url:
        raise HTTPException(
            status_code=400,
            detail="No app uploaded. Upload your .ipa first on the Cloud page.",
        )

    device_name = body.device_name or settings.browserstack_device
    os_version = body.os_version or settings.browserstack_os_version

    try:
        from app.services.browserstack_discovery_service import BrowserStackDiscoveryService

        service = BrowserStackDiscoveryService(
            username=settings.browserstack_username,
            access_key=settings.browserstack_access_key,
        )

        snapshot = await service.discover(
            app_url=app_url,
            device_name=device_name,
            os_version=os_version,
        )

        if not snapshot.screens:
            return CloudDiscoveryResponse(
                success=False,
                error="Discovery completed but no screens were captured. The app may not have loaded.",
            )

        # Save to same path that test generation reads from
        snapshot_path = Path(settings.rag_persist_dir) / "discovery_snapshot.json"
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        snapshot.save(str(snapshot_path))

        interactive_count = len(snapshot.all_interactive_elements())
        logger.info(
            "Cloud discovery saved: %d screens, %d interactive elements → %s",
            len(snapshot.screens), interactive_count, snapshot_path,
        )

        screen_details = [
            ScreenDetail(
                name=s.screen_label,
                element_count=len(s.interactive_elements()),
                navigation_path=s.navigation_path,
            )
            for s in snapshot.screens
        ]
        return CloudDiscoveryResponse(
            success=True,
            screen_count=len(snapshot.screens),
            interactive_count=interactive_count,
            screens=screen_details,
        )

    except Exception as e:
        logger.error("Cloud discovery failed: %s", e, exc_info=True)
        return CloudDiscoveryResponse(
            success=False,
            error=str(e),
        )


# ── Video Proxy ────────────────────────────────────────────────────────────────

@router.get("/video/{session_id}")
async def proxy_video(session_id: str):
    """Proxy BrowserStack session video to avoid CORS issues.

    Streams the video from BrowserStack through the backend so the
    frontend can play it directly without cross-origin restrictions.
    """
    bs = get_browserstack_service()
    if not bs:
        raise HTTPException(status_code=503, detail="Cloud not configured")

    try:
        session_info = await bs.get_session(session_id)
        video_url = session_info.get("video_url")
        if not video_url:
            raise HTTPException(status_code=404, detail="Video not available yet")

        # Stream the video from BrowserStack
        async def stream_video():
            async with httpx.AsyncClient() as client:
                async with client.stream("GET", video_url, timeout=60) as resp:
                    async for chunk in resp.aiter_bytes(chunk_size=65536):
                        yield chunk

        return StreamingResponse(
            stream_video(),
            media_type="video/mp4",
            headers={
                "Content-Disposition": f"inline; filename=session_{session_id}.mp4",
                "Cache-Control": "public, max-age=3600",
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Video proxy failed: %s", e)
        raise HTTPException(status_code=502, detail="Failed to fetch video")
