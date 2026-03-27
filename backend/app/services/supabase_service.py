"""Supabase client for database and auth operations."""
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_client = None
_anon_client = None


def get_supabase_client():
    """Returns a Supabase client using the service role key (bypasses RLS)."""
    global _client
    if _client:
        return _client
    from app.core.config import settings
    if settings.supabase_url and settings.supabase_service_role_key:
        from supabase import create_client
        _client = create_client(settings.supabase_url, settings.supabase_service_role_key)
        logger.info("Supabase service-role client initialized")
        return _client
    return None


def get_supabase_anon_client():
    """Returns a Supabase client using the anon key (for auth sign_up/sign_in)."""
    global _anon_client
    if _anon_client:
        return _anon_client
    from app.core.config import settings
    if settings.supabase_url and settings.supabase_anon_key:
        from supabase import create_client
        _anon_client = create_client(settings.supabase_url, settings.supabase_anon_key)
        logger.info("Supabase anon client initialized")
        return _anon_client
    return None


# ── Helpers ────────────────────────────────────────────────────────────────────

def save_test_run(data: Dict[str, Any], user_id: Optional[str] = None) -> Optional[Dict]:
    """Insert a test run record. Returns the inserted row or None."""
    client = get_supabase_client()
    if not client:
        return None
    if user_id:
        data["user_id"] = user_id
    try:
        result = client.table("test_runs").insert(data).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error("Failed to save test run: %s", e)
        return None


def save_suite(data: Dict[str, Any], user_id: Optional[str] = None) -> Optional[Dict]:
    """Insert a suite record. Returns the inserted row or None."""
    client = get_supabase_client()
    if not client:
        return None
    if user_id:
        data["user_id"] = user_id
    try:
        result = client.table("suites").insert(data).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error("Failed to save suite: %s", e)
        return None
