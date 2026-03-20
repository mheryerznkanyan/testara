"""Configuration settings using Pydantic BaseSettings"""
import logging
from pathlib import Path

from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

# Resolve .env relative to project root (two levels up from this file)
_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-5-20250929"
    llm_temperature: float = 0.3
    llm_max_tokens: int = 4096
    rag_persist_dir: str = str(Path(__file__).resolve().parents[3] / "rag_store")
    rag_collection: str = "ios_app"
    rag_embed_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    rag_top_k: int = 10
    port: int = 8000
    host: str = "0.0.0.0"
    project_root: str = ""
    simulator_name: str = "iPhone 17"
    api_title: str = "iOS Test Generator API"
    api_version: str = "2.0.0"

    # App identity used as fallback when the RAG route doesn't receive one
    default_app_name: str = "SampleApp"

    # App bundle ID for Appium test execution
    bundle_id: str = ""

    # Appium discovery settings
    appium_enabled: bool = False
    appium_server_url: str = "http://localhost:4723"
    appium_startup_timeout: int = 30
    appium_discovery_timeout: int = 60
    appium_test_timeout: int = 120

    # Auth: set a non-empty value to require X-API-Key header on all routes
    api_key: str = ""

    # Batch endpoint: max requests per call to prevent runaway LLM usage
    batch_max_size: int = 20

    # Auto-retry: max generation+execution attempts per /generate-and-run call
    auto_retry_max_attempts: int = 3

    class Config:
        env_file = str(_ENV_FILE)
        extra = "ignore"


settings = Settings()
