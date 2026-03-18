"""FastAPI application entry point with lifespan-managed services."""
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.services.enrichment_service import EnrichmentService
from app.services.test_generator import TestGenerator
from app.services.rag_service import RAGService
from app.services.test_runner import TestRunner
from app.api.routes import health, tests, execution, simulators, discovery

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Unprotected paths that bypass API key auth
# ---------------------------------------------------------------------------
_PUBLIC_PATHS = {
    "/", "/health", "/rag/status", "/docs", "/openapi.json", "/redoc",
    "/run-test", "/generate-test-with-rag", "/recordings", "/simulators"
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and teardown application-level services."""
    from langchain_anthropic import ChatAnthropic
    from pathlib import Path

    llm = ChatAnthropic(
        model=settings.anthropic_model,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
        api_key=settings.anthropic_api_key,
    )
    app.state.llm = llm
    app.state.test_generator = TestGenerator(llm=llm)
    app.state.rag_service = RAGService(settings=settings)
    app.state.enrichment_service = EnrichmentService(llm=llm)
    
    # Initialize test runner with recordings directory
    recordings_dir = Path(__file__).parent.parent / "recordings"
    app.state.test_runner = TestRunner(
        recordings_dir=recordings_dir,
        xcode_project=settings.xcode_project,
        xcode_scheme=settings.xcode_scheme,
        xcode_ui_test_target=settings.xcode_ui_test_target,
    )
    
    # Appium discovery service (optional)
    from app.services.appium_discovery_service import AppiumDiscoveryService

    if settings.appium_enabled:
        app.state.appium_service = AppiumDiscoveryService(
            server_url=settings.appium_server_url,
            startup_timeout=settings.appium_startup_timeout,
        )
        logger.info(
            "Appium discovery service initialized (server: %s)", settings.appium_server_url
        )
    else:
        app.state.appium_service = None
        logger.info("Appium discovery disabled (set APPIUM_ENABLED=true to enable)")

    # Lock to prevent Appium discovery while a test is running on the simulator
    app.state.test_execution_lock = asyncio.Lock()

    logger.info("Services initialised. Auth enabled: %s", bool(settings.api_key))
    yield
    # teardown (nothing needed for now)


app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# API key auth middleware (opt-in: only active when API_KEY is configured)
# ---------------------------------------------------------------------------
@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    """Require X-API-Key header when settings.api_key is configured.

    Public paths (health, docs) are always allowed through.
    """
    if settings.api_key and request.url.path not in _PUBLIC_PATHS:
        provided = request.headers.get("X-API-Key", "")
        if provided != settings.api_key:
            logger.warning(
                "Unauthorized request to %s from %s",
                request.url.path,
                request.client.host if request.client else "unknown",
            )
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid or missing X-API-Key header."},
            )
    return await call_next(request)


app.include_router(health.router)
app.include_router(tests.router)
app.include_router(execution.router)
app.include_router(simulators.router)
app.include_router(discovery.router)

# Mount static files for video recordings
from pathlib import Path
recordings_dir = Path(__file__).parent.parent / "recordings"
recordings_dir.mkdir(parents=True, exist_ok=True)
app.mount("/recordings", StaticFiles(directory=str(recordings_dir)), name="recordings")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)
