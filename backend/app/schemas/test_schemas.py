"""Request and Response schemas for the iOS Test Generator API"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class AppContext(BaseModel):
    app_name: Optional[str] = Field(None, description="Name of the iOS app")
    screens: Optional[List[str]] = Field(None, description="List of screen/view controller names")
    ui_elements: Optional[Dict[str, List[str]]] = Field(
        None,
        description="UI elements grouped by screen",
    )
    accessibility_ids: Optional[List[str]] = Field(None, description="Known accessibility identifiers")
    custom_types: Optional[List[str]] = Field(None, description="Custom view types or components")
    source_code_snippets: Optional[str] = Field(None, description="Relevant Swift source code snippets")


class TestGenerationRequest(BaseModel):
    test_description: str = Field(..., description="Natural language description of what to test")
    test_type: str = Field(..., description="Type of test: 'unit' or 'ui'")
    app_context: Optional[AppContext] = Field(None, description="Context about the app")
    class_name: Optional[str] = Field(None, description="Custom class name for the test")
    include_comments: bool = Field(True, description="Include explanatory comments in generated code")


class TestGenerationResponse(BaseModel):
    swift_code: str
    test_type: str
    class_name: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RAGTestGenerationRequest(BaseModel):
    test_description: str = Field(..., description="Natural language description of what to test (free-form)")
    test_type: str = Field(default="ui", description="Type of test: 'unit' or 'ui'")
    class_name: Optional[str] = Field(None, description="Custom class name for the test")
    include_comments: bool = Field(True, description="Include explanatory comments in generated code")
    rag_top_k: Optional[int] = Field(None, description="Number of RAG documents to retrieve (default: 10)")
    app_name: Optional[str] = Field(
        None,
        description="iOS app name injected into the test context. Falls back to DEFAULT_APP_NAME in config.",
    )
    discovery_enabled: bool = Field(False, description="Use live Appium accessibility discovery before generation")
    bundle_id: Optional[str] = Field(None, description="App bundle ID for Appium discovery e.g. com.example.MyApp")
    device_udid: Optional[str] = Field(None, description="Simulator UDID for Appium discovery (auto-detected if omitted)")
