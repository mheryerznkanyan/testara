"""Configuration settings using Pydantic BaseSettings"""
from pathlib import Path

from pydantic_settings import BaseSettings

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

    # Xcode project path for running tests
    xcode_project: str = ""
    xcode_scheme: str = "SampleApp"
    xcode_ui_test_target: str = "SampleAppUITests"

    # Auth: set a non-empty value to require X-API-Key header on all routes
    api_key: str = ""

    # Batch endpoint: max requests per call to prevent runaway LLM usage
    batch_max_size: int = 20

    class Config:
        env_file = str(_ENV_FILE)
        extra = "ignore"


settings = Settings()
