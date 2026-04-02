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
    llm_temperature: float = 0.0
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
    device_server_url: str = ""  # e.g. http://195.82.45.157:4724
    appium_startup_timeout: int = 30
    appium_discovery_timeout: int = 60
    appium_test_timeout: int = 120

    # Test credentials for auto-login (used by discovery and test runner)
    test_credentials_email: str = ""
    test_credentials_password: str = ""

    # LangSmith tracing
    langsmith_api_key: str = ""
    langsmith_project: str = "testara"
    langsmith_tracing: bool = True

    # Auth: set a non-empty value to require X-API-Key header on all routes
    api_key: str = ""

    # BrowserStack App Automate (cloud execution)
    browserstack_username: str = ""
    browserstack_access_key: str = ""
    # bs:// app URL from a prior upload, or leave empty to upload on first run
    browserstack_app_url: str = ""
    # Default device for cloud runs
    browserstack_device: str = "iPhone 14"
    browserstack_os_version: str = "16"
    # Path to .ipa for auto-upload (optional)
    browserstack_ipa_path: str = ""

    # Supabase
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""

    # Batch endpoint: max requests per call to prevent runaway LLM usage
    batch_max_size: int = 20

    class Config:
        env_file = str(_ENV_FILE)
        extra = "ignore"


settings = Settings()
