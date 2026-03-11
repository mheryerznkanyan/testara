"""LLM-as-judge test to evaluate enrichment quality with app context"""
import pytest
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import settings
from app.services.enrichment_service import EnrichmentService
from app.services.rag_service import RAGService
from app.services.context_extractor import AppContextExtractor


LLM_JUDGE_PROMPT = """You are an expert test quality evaluator. Your job is to judge the quality of test enrichments.

You will be given:
1. Original test description (brief)
2. Enriched test description (expanded)
3. Whether app context was used

Evaluate the enriched description on:
- **Specificity**: Does it reference specific screens, flows, or UI elements?
- **Completeness**: Does it include setup, actions, and verification steps?
- **Actionability**: Can a developer understand exactly what to test?
- **Context Awareness**: Does it show understanding of the app's structure?

Rate from 1-10 and provide brief reasoning.

Output JSON format:
{
  "score": 8,
  "reasoning": "Specific screen names used, includes navigation steps, verifies state",
  "specificity": 9,
  "completeness": 8,
  "actionability": 8,
  "context_awareness": 7
}

Only output valid JSON, no other text.
"""


class TestEnrichmentQuality:
    """Test enrichment quality with LLM as judge"""
    
    @pytest.fixture
    def llm(self):
        """LLM for enrichment"""
        return ChatAnthropic(
            model=settings.anthropic_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            api_key=settings.anthropic_api_key,
        )
    
    @pytest.fixture
    def judge_llm(self):
        """LLM for judging quality"""
        return ChatAnthropic(
            model="claude-opus-4-6",  # Use best model for judging
            temperature=0,  # Deterministic
            api_key=settings.anthropic_api_key,
        )
    
    @pytest.fixture
    def enrichment_service_no_context(self, llm):
        """Enrichment service without app context"""
        return EnrichmentService(llm, app_context_path=None)
    
    @pytest.fixture
    def enrichment_service_with_context(self, llm, tmp_path):
        """Enrichment service with app context"""
        # Create mock app context
        context_file = tmp_path / "APP_CONTEXT.md"
        context_file.write_text("""# App Context

## Overview
A shopping app where users browse items, add to cart, and checkout.

## Main Features
1. **Authentication**
   - Login with email/password at LoginView
   - Test credentials: test@example.com / password123
   
2. **Item Browsing**
   - ItemListView shows all items after login
   - Each item has title, price, category
   - Tap item to navigate to ItemDetailView

## Navigation
- Entry: LoginView
- After login: TabView with Items tab (default), Profile tab
- Pattern: NavigationStack for push navigation

## Common Flows
- Login → ItemListView → Select item → ItemDetailView
""")
        return EnrichmentService(llm, app_context_path=str(context_file))
    
    def judge_quality(self, judge_llm, original: str, enriched: str, has_context: bool) -> dict:
        """Use LLM to judge enrichment quality"""
        messages = [
            SystemMessage(content=LLM_JUDGE_PROMPT),
            HumanMessage(content=f"""
Original: {original}
Enriched: {enriched}
Context Used: {"Yes" if has_context else "No"}

Evaluate and return JSON with scores.
""")
        ]
        
        response = judge_llm.invoke(messages)
        
        # Parse JSON response
        import json
        try:
            # Extract JSON from response
            content = response.content.strip()
            # Handle potential markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            result = json.loads(content)
            return result
        except Exception as e:
            pytest.fail(f"Failed to parse judge response: {e}\nResponse: {response.content}")
    
    @pytest.mark.parametrize("description", [
        "test login",
        "verify item list",
        "check profile screen",
        "test add to cart",
    ])
    def test_context_improves_enrichment(
        self,
        description,
        enrichment_service_no_context,
        enrichment_service_with_context,
        judge_llm
    ):
        """Test that app context improves enrichment quality (LLM as judge)"""
        
        # Enrich without context
        result_no_context = enrichment_service_no_context.enrich(description)
        enriched_no_context = result_no_context["enriched"]
        
        # Enrich with context
        result_with_context = enrichment_service_with_context.enrich(description)
        enriched_with_context = result_with_context["enriched"]
        
        # Judge both
        score_no_context = self.judge_quality(
            judge_llm, description, enriched_no_context, has_context=False
        )
        score_with_context = self.judge_quality(
            judge_llm, description, enriched_with_context, has_context=True
        )
        
        # Print results for visibility
        print(f"\n{'='*60}")
        print(f"Test Description: {description}")
        print(f"{'='*60}")
        print(f"\nWithout Context:")
        print(f"  Enriched: {enriched_no_context[:100]}...")
        print(f"  Score: {score_no_context['score']}/10")
        print(f"  Reasoning: {score_no_context['reasoning']}")
        
        print(f"\nWith Context:")
        print(f"  Enriched: {enriched_with_context[:100]}...")
        print(f"  Score: {score_with_context['score']}/10")
        print(f"  Reasoning: {score_with_context['reasoning']}")
        
        # Assert improvement
        assert score_with_context["score"] >= score_no_context["score"], (
            f"Context should improve or maintain quality. "
            f"Without: {score_no_context['score']}, With: {score_with_context['score']}"
        )
        
        # Context-aware version should score higher on context_awareness
        assert score_with_context["context_awareness"] > score_no_context["context_awareness"], (
            f"Context-aware enrichment should have higher context_awareness score. "
            f"Without: {score_no_context['context_awareness']}, "
            f"With: {score_with_context['context_awareness']}"
        )
    
    def test_context_adds_screen_names(
        self,
        enrichment_service_with_context
    ):
        """Test that context causes enrichment to include actual screen names"""
        
        result = enrichment_service_with_context.enrich("test login")
        enriched = result["enriched"]
        
        # Should mention LoginView (from context)
        assert "LoginView" in enriched or "login screen" in enriched.lower(), (
            f"Enrichment should reference login screen. Got: {enriched}"
        )
        
        # Should mention post-login screen (ItemListView or items)
        assert "ItemListView" in enriched or "items" in enriched.lower(), (
            f"Enrichment should reference items screen. Got: {enriched}"
        )
    
    def test_context_adds_credentials(
        self,
        enrichment_service_with_context
    ):
        """Test that context includes test credentials"""
        
        result = enrichment_service_with_context.enrich("test login with valid credentials")
        enriched = result["enriched"]
        
        # Should reference credentials or specific login values
        has_creds = (
            "test@example.com" in enriched or
            "password123" in enriched or
            "valid username" in enriched.lower() and "valid password" in enriched.lower()
        )
        
        assert has_creds, f"Enrichment should reference credentials. Got: {enriched}"
    
    def test_context_adds_navigation_flow(
        self,
        enrichment_service_with_context
    ):
        """Test that context includes navigation steps"""
        
        result = enrichment_service_with_context.enrich("check item details")
        enriched = result["enriched"]
        
        # Should mention need to login first or navigate from items list
        mentions_flow = (
            "login" in enriched.lower() or
            "items list" in enriched.lower() or
            "ItemListView" in enriched or
            "navigate" in enriched.lower()
        )
        
        assert mentions_flow, (
            f"Enrichment should include navigation context. Got: {enriched}"
        )


class TestContextExtraction:
    """Test context extraction from RAG index"""
    
    @pytest.fixture
    def rag_service(self):
        """RAG service with mock data"""
        from unittest.mock import Mock
        
        rag = Mock(spec=RAGService)
        
        # Mock query responses
        def mock_query(query_text, k=10):
            if "navigation" in query_text.lower():
                return {
                    "code_snippets": [
                        {"path": "App.swift", "content": "@main struct MyApp: App { LoginView() }"},
                        {"path": "ContentView.swift", "content": "TabView { ItemsTab() ProfileTab() }"},
                        {"path": "ItemListView.swift", "content": "NavigationLink { ItemDetailView() }"},
                    ]
                }
            elif "screen" in query_text.lower() or "view" in query_text.lower():
                return {
                    "code_snippets": [
                        {"path": "Views/LoginView.swift", "content": "struct LoginView: View"},
                        {"path": "Views/ItemListView.swift", "content": "struct ItemListView: View"},
                        {"path": "Views/ProfileView.swift", "content": "struct ProfileView: View"},
                    ]
                }
            elif "accessibility" in query_text.lower():
                return {
                    "code_snippets": [
                        {"path": "LoginView.swift", "content": '.accessibilityIdentifier("loginButton")'},
                        {"path": "LoginView.swift", "content": '.accessibilityIdentifier("emailTextField")'},
                    ]
                }
            else:
                return {"code_snippets": []}
        
        rag.query = mock_query
        return rag
    
    def test_extract_screens(self, rag_service):
        """Test screen extraction"""
        extractor = AppContextExtractor(rag_service)
        
        screens = extractor._extract_screens()
        
        assert "LoginView" in screens
        assert "ItemListView" in screens
        assert "ProfileView" in screens
    
    def test_extract_navigation(self, rag_service):
        """Test navigation pattern extraction"""
        extractor = AppContextExtractor(rag_service)
        
        nav_info = extractor._extract_navigation()
        
        assert len(nav_info["patterns"]) > 0
        assert any("Tab" in p for p in nav_info["patterns"])
        assert any("NavigationLink" in p for p in nav_info["patterns"])
    
    def test_extract_ui_elements(self, rag_service):
        """Test UI element extraction"""
        extractor = AppContextExtractor(rag_service)
        
        elements = extractor._extract_ui_elements()
        
        assert "`loginButton`" in elements
        assert "`emailTextField`" in elements
    
    def test_generate_context_document(self, rag_service):
        """Test full context document generation"""
        extractor = AppContextExtractor(rag_service)
        
        context = extractor.extract_context()
        
        # Should be valid markdown
        assert context.startswith("# App Context")
        assert "## Screens" in context
        assert "## Navigation Patterns" in context
        assert "LoginView" in context
        assert "TabView" in context or "NavigationLink" in context
