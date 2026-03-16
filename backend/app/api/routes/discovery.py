"""Appium accessibility discovery routes"""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()


class DiscoveryRequest(BaseModel):
    bundle_id: str
    device_udid: str
    screen_hints: Optional[list[str]] = None


class ElementSummary(BaseModel):
    element_type: str
    name: str
    label: str
    value: str
    enabled: bool


class DiscoveryResponse(BaseModel):
    success: bool
    bundle_id: str
    element_count: int
    interactive_count: int
    elements: list[ElementSummary]
    has_screenshot: bool
    error: Optional[str] = None


@router.post("/discover", response_model=DiscoveryResponse)
async def discover_accessibility_tree(request: Request, body: DiscoveryRequest):
    """
    Run live Appium discovery to capture the accessibility tree of a running app.
    Returns all interactive elements with their actual runtime accessibility identifiers.
    """
    appium_service = getattr(request.app.state, "appium_service", None)
    if appium_service is None:
        raise HTTPException(
            status_code=503,
            detail="Appium discovery not enabled. Set APPIUM_ENABLED=true in .env",
        )

    try:
        snapshot = await appium_service.discover(
            bundle_id=body.bundle_id,
            device_udid=body.device_udid,
            screen_hints=body.screen_hints,
        )

        interactive = snapshot.interactive_elements()

        # Store snapshot in app state for use by test generation
        if not hasattr(request.app.state, "snapshots"):
            request.app.state.snapshots = {}
        snapshot_key = f"{body.bundle_id}:{body.device_udid}"
        request.app.state.snapshots[snapshot_key] = snapshot

        return DiscoveryResponse(
            success=len(interactive) > 0,
            bundle_id=body.bundle_id,
            element_count=len(snapshot.elements),
            interactive_count=len(interactive),
            elements=[
                ElementSummary(
                    element_type=e.element_type,
                    name=e.name,
                    label=e.label,
                    value=e.value,
                    enabled=e.enabled,
                )
                for e in interactive[:100]  # cap at 100 for response size
            ],
            has_screenshot=bool(snapshot.screenshot_b64),
        )

    except Exception as e:
        logger.error("Discovery failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
