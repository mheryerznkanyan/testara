"""Health check routes"""
from fastapi import APIRouter, Request

from app.core.config import settings

router = APIRouter()


@router.get("/")
async def root():
    return {
        "service": settings.api_title,
        "status": "running",
        "version": settings.api_version,
    }


@router.get("/health")
async def health():
    return {
        "status": "healthy",
        "llm_configured": bool(settings.anthropic_api_key),
        "model": settings.anthropic_model,
        "auth_enabled": bool(settings.api_key),
    }


@router.get("/rag/status")
async def rag_status(request: Request):
    """Return vector store health: document count, collection, persist directory."""
    rag_service = request.app.state.rag_service
    return rag_service.status()
