"""Database routes — Supabase CRUD for suites, test runs, and stats."""
import logging
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.services.supabase_service import get_supabase_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/db", tags=["database"])


def _require_client():
    client = get_supabase_client()
    if not client:
        raise HTTPException(status_code=503, detail="Supabase not configured")
    return client


# ── Schemas ────────────────────────────────────────────────────────────────────

class TestRunCreate(BaseModel):
    test_name: str
    suite_id: Optional[str] = None
    suite_name: Optional[str] = None
    suite_test_id: Optional[str] = None
    status: Literal["passed", "failed", "running", "queued"]
    device: Optional[str] = None
    os_version: Optional[str] = None
    duration: Optional[float] = None
    logs: Optional[str] = None
    error_message: Optional[str] = None
    screenshot_url: Optional[str] = None
    execution_mode: Literal["local", "cloud"] = "cloud"


class SuiteCreate(BaseModel):
    name: str
    description: Optional[str] = None


class SuiteUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class SuiteTestCreate(BaseModel):
    name: str
    description: Optional[str] = None
    test_code: str
    class_name: Optional[str] = None
    quality_score: Optional[int] = None
    quality_grade: Optional[str] = None


class SuiteTestUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    test_code: Optional[str] = None
    class_name: Optional[str] = None


# ── Run Stats ──────────────────────────────────────────────────────────────────

@router.get("/run-stats")
async def get_run_stats(user: Optional[dict] = Depends(get_current_user)):
    """Get aggregated test run statistics."""
    client = _require_client()
    try:
        query = client.table("test_runs").select("status, created_at")
        if user:
            query = query.or_(f"user_id.eq.{user['id']},user_id.is.null")

        result = query.execute()
        rows = result.data or []

        total = len(rows)
        passed = sum(1 for r in rows if r["status"] == "passed")
        failed = sum(1 for r in rows if r["status"] == "failed")
        running = sum(1 for r in rows if r["status"] == "running")
        last_run_at = max((r["created_at"] for r in rows), default=None) if rows else None

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "running": running,
            "last_run_at": last_run_at,
        }
    except Exception as e:
        logger.error("Failed to fetch run stats: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch stats")


# ── Test Runs ──────────────────────────────────────────────────────────────────

@router.get("/test-runs")
async def list_test_runs(
    status: Optional[str] = Query(None),
    suite_id: Optional[str] = Query(None),
    suite_test_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    user: Optional[dict] = Depends(get_current_user),
):
    """List test runs with optional status/suite filters."""
    client = _require_client()
    try:
        query = client.table("test_runs").select("*").order("created_at", desc=True).limit(limit)

        if status:
            query = query.eq("status", status)
        if suite_id:
            query = query.eq("suite_id", suite_id)
        if suite_test_id:
            query = query.eq("suite_test_id", suite_test_id)
        if user:
            query = query.or_(f"user_id.eq.{user['id']},user_id.is.null")

        result = query.execute()
        return result.data or []
    except Exception as e:
        logger.error("Failed to list test runs: %s", e)
        raise HTTPException(status_code=500, detail="Failed to list test runs")


@router.post("/test-runs")
async def create_test_run(
    body: TestRunCreate,
    user: Optional[dict] = Depends(get_current_user),
):
    """Insert a test run record."""
    client = _require_client()
    try:
        data = body.model_dump(exclude_none=True)
        if user:
            data["user_id"] = user["id"]

        result = client.table("test_runs").insert(data).execute()
        if not result.data:
            raise HTTPException(status_code=500, detail="Insert returned no data")
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create test run: %s", e)
        raise HTTPException(status_code=500, detail="Failed to create test run")


# ── Suites ─────────────────────────────────────────────────────────────────────

@router.get("/suites")
async def list_suites(user: Optional[dict] = Depends(get_current_user)):
    """List all test suites with aggregated test stats."""
    client = _require_client()
    try:
        query = client.table("suites").select("*").order("created_at", desc=True)
        if user:
            query = query.or_(f"user_id.eq.{user['id']},user_id.is.null")

        result = query.execute()
        suites = result.data or []

        # Batch-fetch test stats for all suites
        suite_ids = [s["id"] for s in suites]
        if suite_ids:
            tests_result = client.table("suite_tests").select("suite_id, last_status").in_("suite_id", suite_ids).execute()
            tests = tests_result.data or []

            # Group by suite_id
            stats: dict = {}
            for t in tests:
                sid = t["suite_id"]
                if sid not in stats:
                    stats[sid] = {"test_count": 0, "passed_count": 0, "failed_count": 0, "not_run_count": 0}
                stats[sid]["test_count"] += 1
                status = t.get("last_status")
                if status == "passed":
                    stats[sid]["passed_count"] += 1
                elif status == "failed":
                    stats[sid]["failed_count"] += 1
                else:
                    stats[sid]["not_run_count"] += 1

            for s in suites:
                s_stats = stats.get(s["id"], {"test_count": 0, "passed_count": 0, "failed_count": 0, "not_run_count": 0})
                s.update(s_stats)
        else:
            for s in suites:
                s.update({"test_count": 0, "passed_count": 0, "failed_count": 0, "not_run_count": 0})

        return suites
    except Exception as e:
        logger.error("Failed to list suites: %s", e)
        raise HTTPException(status_code=500, detail="Failed to list suites")


@router.post("/suites")
async def create_suite(
    body: SuiteCreate,
    user: Optional[dict] = Depends(get_current_user),
):
    """Create a new test suite."""
    client = _require_client()
    try:
        data = body.model_dump(exclude_none=True)
        if user:
            data["user_id"] = user["id"]

        result = client.table("suites").insert(data).execute()
        if not result.data:
            raise HTTPException(status_code=500, detail="Insert returned no data")
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create suite: %s", e)
        raise HTTPException(status_code=500, detail="Failed to create suite")


@router.get("/suites/{suite_id}")
async def get_suite(suite_id: str, user: Optional[dict] = Depends(get_current_user)):
    """Get a single suite with aggregated test stats."""
    client = _require_client()
    try:
        result = client.table("suites").select("*").eq("id", suite_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Suite not found")
        suite = result.data[0]

        # Aggregate stats from suite_tests
        tests_result = client.table("suite_tests").select("last_status").eq("suite_id", suite_id).execute()
        tests = tests_result.data or []

        suite["test_count"] = len(tests)
        suite["passed_count"] = sum(1 for t in tests if t["last_status"] == "passed")
        suite["failed_count"] = sum(1 for t in tests if t["last_status"] == "failed")
        suite["not_run_count"] = sum(1 for t in tests if t["last_status"] in ("not_run", None))

        return suite
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get suite: %s", e)
        raise HTTPException(status_code=500, detail="Failed to get suite")


@router.put("/suites/{suite_id}")
async def update_suite(
    suite_id: str,
    body: SuiteUpdate,
    user: Optional[dict] = Depends(get_current_user),
):
    """Update a suite's name or description."""
    client = _require_client()
    try:
        data = body.model_dump(exclude_none=True)
        if not data:
            raise HTTPException(status_code=400, detail="No fields to update")

        query = client.table("suites").update(data).eq("id", suite_id)
        if user:
            query = query.eq("user_id", user["id"])

        result = query.execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Suite not found")
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update suite: %s", e)
        raise HTTPException(status_code=500, detail="Failed to update suite")


@router.delete("/suites/{suite_id}")
async def delete_suite(suite_id: str, user: Optional[dict] = Depends(get_current_user)):
    """Delete a suite (cascades to suite_tests)."""
    client = _require_client()
    try:
        query = client.table("suites").delete().eq("id", suite_id)
        if user:
            query = query.eq("user_id", user["id"])

        result = query.execute()
        return {"deleted": True}
    except Exception as e:
        logger.error("Failed to delete suite: %s", e)
        raise HTTPException(status_code=500, detail="Failed to delete suite")


# ── Suite Tests ───────────────────────────────────────────────────────────────

@router.get("/suites/{suite_id}/tests")
async def list_suite_tests(suite_id: str, user: Optional[dict] = Depends(get_current_user)):
    """List all tests in a suite ordered by position."""
    client = _require_client()
    try:
        query = (
            client.table("suite_tests")
            .select("*")
            .eq("suite_id", suite_id)
            .order("position")
        )
        result = query.execute()
        return result.data or []
    except Exception as e:
        logger.error("Failed to list suite tests: %s", e)
        raise HTTPException(status_code=500, detail="Failed to list suite tests")


@router.post("/suites/{suite_id}/tests")
async def create_suite_test(
    suite_id: str,
    body: SuiteTestCreate,
    user: Optional[dict] = Depends(get_current_user),
):
    """Add a test to a suite."""
    client = _require_client()
    try:
        # Auto-compute position
        existing = (
            client.table("suite_tests")
            .select("position")
            .eq("suite_id", suite_id)
            .order("position", desc=True)
            .limit(1)
            .execute()
        )
        next_pos = (existing.data[0]["position"] + 1) if existing.data else 0

        data = body.model_dump(exclude_none=True)
        data["suite_id"] = suite_id
        data["position"] = next_pos
        data["last_status"] = "not_run"
        if user:
            data["user_id"] = user["id"]

        result = client.table("suite_tests").insert(data).execute()
        if not result.data:
            raise HTTPException(status_code=500, detail="Insert returned no data")
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create suite test: %s", e)
        raise HTTPException(status_code=500, detail="Failed to create suite test")


@router.put("/suites/{suite_id}/tests/{test_id}")
async def update_suite_test(
    suite_id: str,
    test_id: str,
    body: SuiteTestUpdate,
    user: Optional[dict] = Depends(get_current_user),
):
    """Update a test within a suite."""
    client = _require_client()
    try:
        data = body.model_dump(exclude_none=True)
        if not data:
            raise HTTPException(status_code=400, detail="No fields to update")

        query = (
            client.table("suite_tests")
            .update(data)
            .eq("id", test_id)
            .eq("suite_id", suite_id)
        )
        if user:
            query = query.eq("user_id", user["id"])

        result = query.execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Suite test not found")
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update suite test: %s", e)
        raise HTTPException(status_code=500, detail="Failed to update suite test")


@router.delete("/suites/{suite_id}/tests/{test_id}")
async def delete_suite_test(
    suite_id: str,
    test_id: str,
    user: Optional[dict] = Depends(get_current_user),
):
    """Remove a test from a suite."""
    client = _require_client()
    try:
        query = (
            client.table("suite_tests")
            .delete()
            .eq("id", test_id)
            .eq("suite_id", suite_id)
        )
        if user:
            query = query.eq("user_id", user["id"])

        query.execute()
        return {"deleted": True}
    except Exception as e:
        logger.error("Failed to delete suite test: %s", e)
        raise HTTPException(status_code=500, detail="Failed to delete suite test")


@router.post("/suites/{suite_id}/tests/{test_id}/run")
async def run_single_suite_test(
    suite_id: str,
    test_id: str,
    request_obj: "Request" = None,
    user: Optional[dict] = Depends(get_current_user),
):
    """Run a single test from a suite and update its status."""
    from fastapi import Request as _Req
    client = _require_client()
    try:
        # Fetch the test
        test_result = (
            client.table("suite_tests")
            .select("*")
            .eq("id", test_id)
            .eq("suite_id", suite_id)
            .execute()
        )
        if not test_result.data:
            raise HTTPException(status_code=404, detail="Suite test not found")

        test = test_result.data[0]

        # Mark as running
        client.table("suite_tests").update({"last_status": "running"}).eq("id", test_id).execute()

        return {"test_id": test_id, "suite_id": suite_id, "status": "running", "test_code": test["test_code"]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to start suite test run: %s", e)
        raise HTTPException(status_code=500, detail="Failed to run suite test")
