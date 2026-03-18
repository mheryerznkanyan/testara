"""Configuration settings using Pydantic BaseSettings"""
import logging
import re
from pathlib import Path

from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

# Resolve .env relative to project root (two levels up from this file)
_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


def _find_xcodeproj(project_root: str) -> str:
    """Auto-detect .xcodeproj inside PROJECT_ROOT (excluding Pods)."""
    if not project_root:
        return ""
    matches = [
        p for p in Path(project_root).glob("*.xcodeproj")
        if "Pods.xcodeproj" not in str(p)
    ]
    if matches:
        logger.info(f"Auto-detected Xcode project: {matches[0]}")
        return str(matches[0])
    return ""


def _infer_scheme(xcodeproj: str) -> str:
    """Find the main app scheme from xcshareddata."""
    if not xcodeproj:
        return ""
    project_name = Path(xcodeproj).stem
    schemes_dir = Path(xcodeproj) / "xcshareddata" / "xcschemes"
    if schemes_dir.exists():
        # Prefer scheme matching project name
        exact = schemes_dir / f"{project_name}.xcscheme"
        if exact.exists():
            return project_name
        # Fallback: first non-test scheme
        for s in schemes_dir.glob("*.xcscheme"):
            if "Test" not in s.stem:
                return s.stem
    return project_name  # default assumption


def _find_ui_test_target(xcodeproj: str) -> str:
    """Find actual UI test target name from project.pbxproj."""
    if not xcodeproj:
        return ""
    pbxproj_path = Path(xcodeproj) / "project.pbxproj"
    if not pbxproj_path.exists():
        return Path(xcodeproj).stem + "UITests"
    try:
        lines = pbxproj_path.read_text().splitlines()
        for i, line in enumerate(lines):
            if 'product-type.bundle.ui-testing' in line:
                # Walk backwards to find the target block header
                for j in range(i - 1, max(i - 50, 0), -1):
                    m = re.match(r'\s*\w+\s*/\*\s*(.+?)\s*\*/\s*=\s*\{', lines[j])
                    if m:
                        return m.group(1)
    except Exception as e:
        logger.warning(f"Could not parse pbxproj for UI test target: {e}")
    return Path(xcodeproj).stem + "UITests"


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

    # Xcode project path for running tests (auto-detected from PROJECT_ROOT if empty)
    xcode_project: str = ""
    xcode_scheme: str = ""
    xcode_ui_test_target: str = ""

    # Appium discovery settings
    appium_enabled: bool = False
    appium_server_url: str = "http://localhost:4723"
    appium_startup_timeout: int = 30
    appium_discovery_timeout: int = 60

    # Test credentials: injected into prompt so LLM can generate login steps
    test_credentials_email: str = ""
    test_credentials_password: str = ""

    # Launch environment: key=value pairs passed to the app via launchEnvironment
    # Use this to disable heavy SDKs (Sentry, Firebase, etc.) that cause main thread stalls
    # Format: "KEY1=VALUE1,KEY2=VALUE2"  e.g. "EMERGE_IS_RUNNING_FOR_SNAPSHOTS=1,DISABLE_ANALYTICS=1"
    launch_environment: str = ""

    # Auth: set a non-empty value to require X-API-Key header on all routes
    api_key: str = ""

    # Batch endpoint: max requests per call to prevent runaway LLM usage
    batch_max_size: int = 20

    class Config:
        env_file = str(_ENV_FILE)
        extra = "ignore"


settings = Settings()

# Auto-detect Xcode settings from PROJECT_ROOT when not explicitly set
if not settings.xcode_project:
    settings.xcode_project = _find_xcodeproj(settings.project_root)
if not settings.xcode_scheme:
    settings.xcode_scheme = _infer_scheme(settings.xcode_project)
if not settings.xcode_ui_test_target:
    settings.xcode_ui_test_target = _find_ui_test_target(settings.xcode_project)
