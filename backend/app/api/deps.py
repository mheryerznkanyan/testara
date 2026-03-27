"""FastAPI dependencies for auth and user extraction."""
import logging
from typing import Optional

from fastapi import HTTPException, Request

logger = logging.getLogger(__name__)


async def get_current_user(request: Request) -> Optional[dict]:
    """Extract and validate JWT from Authorization header.

    Returns user dict {id, email} or None if no token provided.
    Raises 401 if token is present but invalid.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None

    token = auth_header[7:]
    from app.services.supabase_service import get_supabase_client

    client = get_supabase_client()
    if not client:
        return None

    try:
        user_response = client.auth.get_user(token)
        user = user_response.user
        return {"id": str(user.id), "email": user.email}
    except Exception as e:
        logger.warning("JWT validation failed: %s", e)
        raise HTTPException(status_code=401, detail="Invalid or expired token")


async def require_user(request: Request) -> dict:
    """Same as get_current_user but raises 401 if not authenticated."""
    user = await get_current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user
