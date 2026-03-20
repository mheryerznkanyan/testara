"""Test generation routes"""
import asyncio
import logging
from typing import List

from fastapi import APIRouter, HTTPException, Request

from app.core.config import settings
from app.schemas.test_schemas import (
    AppContext,
    TestGenerationRequest,
    TestGenerationResponse,
    RAGTestGenerationRequest,
)
from app.services.navigation_service import NavigationService

logger = logging.getLogger(__name__)

router = APIRouter()


async def _enrich(request: Request, description: str) -> dict:
    """Run enrichment in a thread and return the enrichment result dict."""
    svc = request.app.state.enrichment_service
    return await asyncio.to_thread(svc.enrich, description)


@router.post("/generate-test-with-rag", response_model=TestGenerationResponse)
async def generate_test_with_rag(request: Request, body: RAGTestGenerationRequest):
    """Generate a test using RAG context.

    The description is enriched before the RAG query and test generation steps,
    so both retrieval quality and generated test quality benefit.
    """
    test_type = body.test_type.lower().strip()
    if test_type not in {"unit", "ui"}:
        raise HTTPException(status_code=400, detail="test_type must be 'unit' or 'ui'")

    # Enrich first — better description → better RAG retrieval
    enrichment = await _enrich(request, body.test_description)
    enriched_description = enrichment["enriched"]

    rag_service = request.app.state.rag_service
    rag_context = rag_service.query(enriched_description, k=body.rag_top_k)

    code_snippets_text = "\n\n".join(
        f"// {s['kind']} from {s['path']}\n{s['content']}"
        for s in rag_context["code_snippets"]
    )

    # Extract and inject navigation context (like v1 did)
    navigation_context_str = ""
    navigation_metadata = {}
    if settings.project_root:
        try:
            nav_service = NavigationService(settings.project_root)
            await asyncio.to_thread(nav_service.extract)
            navigation_context_str = nav_service.format_for_prompt(enriched_description)
            if navigation_context_str:
                code_snippets_text = f"{navigation_context_str}\n\n{code_snippets_text}"
                navigation_metadata["navigation_context_used"] = True
                logger.info("Navigation context injected into prompt")
        except Exception as e:
            logger.warning("Failed to extract navigation context: %s", e)
            navigation_metadata["navigation_context_error"] = str(e)

    resolved_app_name = body.app_name or settings.default_app_name

    app_context = AppContext(
        app_name=resolved_app_name,
        screens=rag_context["screens"],
        accessibility_ids=rag_context["accessibility_ids"],
        source_code_snippets=code_snippets_text or None,
    )

    gen_request = TestGenerationRequest(
        test_description=enriched_description,
        test_type=test_type,
        app_context=app_context,
        class_name=body.class_name,
        include_comments=body.include_comments,
    )

    # Load cached discovery snapshot (run /discover once, reuse forever)
    accessibility_snapshot = None
    from pathlib import Path
    from app.utils.accessibility_tree_parser import MultiScreenSnapshot

    snapshot_path = Path(settings.rag_persist_dir) / "discovery_snapshot.json"
    if snapshot_path.exists():
        try:
            accessibility_snapshot = MultiScreenSnapshot.load(str(snapshot_path))
            logger.info(
                "Loaded cached discovery snapshot: %d screens, %d interactive elements",
                len(accessibility_snapshot.screens),
                len(accessibility_snapshot.interactive_elements()),
            )
        except Exception as e:
            logger.warning("Could not load cached snapshot: %s", e)

    # Fall back to live discovery if no cache and discovery is enabled
    if accessibility_snapshot is None and body.discovery_enabled:
        effective_bundle_id = body.bundle_id or settings.bundle_id
        effective_device_udid = body.device_udid or ""

        # Auto-detect booted simulator if no UDID provided
        if effective_bundle_id and not effective_device_udid:
            try:
                import subprocess, json as _json
                raw = subprocess.check_output(
                    ["xcrun", "simctl", "list", "devices", "booted", "--json"],
                    timeout=5,
                )
                device_data = _json.loads(raw)
                for runtime, devices in device_data.get("devices", {}).items():
                    for d in devices:
                        if d.get("state") == "Booted":
                            effective_device_udid = d["udid"]
                            break
                    if effective_device_udid:
                        break
            except Exception as e:
                logger.warning("Could not auto-detect booted simulator: %s", e)

        if effective_bundle_id and effective_device_udid:
            appium_service = getattr(request.app.state, "appium_service", None)
            if appium_service:
                try:
                    accessibility_snapshot = await appium_service.discover(
                        bundle_id=effective_bundle_id,
                        device_udid=effective_device_udid,
                    )
                    logger.info(
                        "Appium discovery complete: %d interactive elements",
                        len(accessibility_snapshot.interactive_elements()),
                    )
                    # Save to disk for future reuse
                    try:
                        accessibility_snapshot.save(str(snapshot_path))
                    except Exception:
                        pass
                except Exception as e:
                    logger.warning("Appium discovery failed (continuing without): %s", e)
            else:
                logger.warning(
                    "discovery_enabled=True but Appium service not initialized (APPIUM_ENABLED=false)"
                )

    generator = request.app.state.test_generator
    try:
        response = await asyncio.to_thread(
            generator.run, gen_request, accessibility_snapshot
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error generating test: {exc}")

    response.metadata["enrichment"] = {
        "original_description": body.test_description,
        "enriched_description": enriched_description,
        "enrichment_used": enrichment["used"],
        **({"enrichment_error": enrichment["error"]} if "error" in enrichment else {}),
    }

    response.metadata["rag_enabled"] = True
    response.metadata["rag_context"] = {
        "accessibility_ids_found": len(rag_context.get("accessibility_ids", [])),
        "screens_found": len(rag_context.get("screens", [])),
        "code_snippets_used": len(rag_context.get("code_snippets", [])),
        "total_docs_retrieved": rag_context.get("total_docs_retrieved", 0),
    }
    if "error" in rag_context:
        response.metadata["rag_error"] = rag_context["error"]
    if navigation_metadata:
        response.metadata["navigation"] = navigation_metadata

    return response


@router.post("/generate-tests-batch")
async def generate_tests_batch(request: Request, bodies: List[TestGenerationRequest]):
    """Generate multiple tests in parallel using asyncio.gather.

    Capped at ``settings.batch_max_size`` requests per call.
    Each description is enriched independently before generation.
    """
    if len(bodies) > settings.batch_max_size:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Batch size {len(bodies)} exceeds the maximum of "
                f"{settings.batch_max_size}. Split your request into smaller batches."
            ),
        )

    # Enrich all descriptions in parallel
    enrichments = await asyncio.gather(
        *[_enrich(request, req.test_description) for req in bodies],
        return_exceptions=True,
    )

    enriched_bodies = []
    for req, enc in zip(bodies, enrichments):
        if isinstance(enc, Exception):
            enriched_bodies.append(req)  # fallback: use original
        else:
            enriched_bodies.append(req.model_copy(update={"test_description": enc["enriched"]}))

    generator = request.app.state.test_generator

    results_raw = await asyncio.gather(
        *[asyncio.to_thread(generator.run, req) for req in enriched_bodies],
        return_exceptions=True,
    )

    results = []
    errors = []
    for idx, item in enumerate(results_raw):
        if isinstance(item, Exception):
            errors.append({
                "index": idx,
                "error": str(item),
                "description": (bodies[idx].test_description or "")[:100],
            })
        else:
            enc = enrichments[idx]
            if not isinstance(enc, Exception):
                item.metadata["enrichment"] = {
                    "original_description": enc["original"],
                    "enriched_description": enc["enriched"],
                }
            results.append(item)

    return {
        "generated": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors,
    }
