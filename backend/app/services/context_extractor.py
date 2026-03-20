"""Auto-generate APP_CONTEXT.md from RAG index"""
import logging
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)


class AppContextExtractor:
    """Extract app context from RAG index to create APP_CONTEXT.md"""
    
    def __init__(self, rag_service):
        self.rag_service = rag_service
    
    def extract_context(self) -> str:
        """Generate APP_CONTEXT.md content from RAG index"""
        try:
            # Get all indexed data
            screens = self._extract_screens()
            navigation = self._extract_navigation()
            ui_elements = self._extract_ui_elements()
            sample_code = self._extract_sample_code()
            
            # Build markdown document
            context = self._build_context_doc(screens, navigation, ui_elements, sample_code)
            
            logger.info("Generated app context from RAG index")
            return context
            
        except Exception as e:
            logger.error(f"Failed to extract app context: {e}")
            return self._get_template()
    
    # Chunk kinds that represent user-facing screens
    _SCREEN_KINDS = {"swiftui_view", "screen_card", "uikit_viewcontroller"}

    def _extract_screens(self) -> List[str]:
        """Extract screen/view names from RAG index.

        Accepts any chunk whose ``kind`` is a screen type (SwiftUI view,
        UIKit view-controller, or screen-card).  No name-based filtering
        so that apps using *Screen, *Page, *Content, or any other naming
        convention are discovered automatically.
        """
        try:
            result = self.rag_service.query(
                "View Screen Page body NavigationStack TabView", k=30
            )

            logger.info(
                "Screen query returned %d snippets",
                len(result.get("code_snippets", [])),
            )

            screens: set[str] = set()

            for snippet in result.get("code_snippets", []):
                screen_name = snippet.get("screen")
                kind = snippet.get("kind")

                if screen_name and kind in self._SCREEN_KINDS:
                    screens.add(screen_name)

            # Also pull from the top-level "screens" list returned by RAG
            for screen in result.get("screens", []):
                if screen:
                    screens.add(screen)

            logger.info("Extracted %d screens", len(screens))
            return sorted(screens)

        except Exception as e:
            logger.warning("Failed to extract screens: %s", e)
            return []
    
    # Standard Apple framework navigation constructs to detect.
    # Each entry: (search_token, dedup_key, label)
    _NAV_PATTERNS = [
        ("NavigationStack",         "NavStack",   "NavigationStack (push navigation)"),
        ("NavigationLink",          "NavStack",   "NavigationStack (push navigation)"),
        ("TabView",                 "TabView",    "TabView (tab-based navigation)"),
        (".sheet(",                 "Sheet",      "Modal sheets"),
        (".fullScreenCover(",       "FSCover",    "Full-screen covers"),
        ("UINavigationController",  "UINav",      "UINavigationController (UIKit push)"),
        ("UITabBarController",      "UITab",      "UITabBarController (UIKit tabs)"),
        ("performSegue(",           "Segue",      "Storyboard segues"),
    ]

    def _extract_navigation(self) -> Dict:
        """Extract navigation patterns from indexed code.

        Uses only standard Apple framework constructs — no app-specific
        screen names are referenced.  Runs two queries: one for navigation
        constructs and one for the @main entry point (which may be chunked
        as a plain struct rather than a view).
        """
        import re

        try:
            nav_info: Dict = {
                "patterns": [],
                "entry_screen": None,
                "tabs": [],
            }
            seen: set[str] = set()

            # Two queries: navigation constructs + app entry point
            nav_result = self.rag_service.query(
                "TabView NavigationStack sheet tabItem body", k=15
            )
            entry_result = self.rag_service.query(
                "@main App WindowGroup Scene body", k=5
            )

            all_snippets = (
                nav_result.get("code_snippets", [])
                + entry_result.get("code_snippets", [])
            )

            for snippet in all_snippets:
                content = snippet.get("content", "")
                screen_name = snippet.get("screen", "")

                # Detect standard navigation constructs
                for token, key, label in self._NAV_PATTERNS:
                    if token in content and key not in seen:
                        nav_info["patterns"].append(label)
                        seen.add(key)

                # Extract tab names from tabItem blocks.
                # Handles both Label("Name", ...) and Image(systemName: "icon")
                if "tabItem" in content:
                    # Try Label("Name", ...) first
                    for m in re.finditer(r'Label\(\s*"([^"]+)"', content):
                        tab_name = m.group(1)
                        if tab_name not in nav_info["tabs"]:
                            nav_info["tabs"].append(tab_name)

                    # Fallback: extract the screen/view name before .tabItem
                    # e.g.  FeedScreen(...)\n  .tabItem {
                    if not nav_info["tabs"]:
                        for m in re.finditer(
                            r'(\w+(?:Screen|View|Tab|Page))\s*\(.*?\).*?\.tabItem',
                            content, re.DOTALL,
                        ):
                            tab_name = m.group(1)
                            if tab_name not in nav_info["tabs"]:
                                nav_info["tabs"].append(tab_name)

                # Infer entry screen from @main App struct or WindowGroup
                if not nav_info["entry_screen"]:
                    if "@main" in content or "WindowGroup" in content:
                        nav_info["entry_screen"] = screen_name or None

            return nav_info

        except Exception as e:
            logger.warning("Failed to extract navigation: %s", e)
            return {"patterns": [], "entry_screen": None, "tabs": []}
    
    def _extract_ui_elements(self) -> List[str]:
        """Extract accessibility identifiers from the RAG index.

        Queries for accessibility_map chunks which list IDs line-by-line.
        The query is generic — no app-specific keywords.
        """
        try:
            result = self.rag_service.query(
                "ACCESSIBILITY_IDS accessibilityIdentifier", k=25
            )

            logger.info(
                "UI elements query returned %d snippets",
                len(result.get("code_snippets", [])),
            )

            elements: list[str] = []
            for snippet in result.get("code_snippets", []):
                kind = snippet.get("kind", "")
                content = snippet.get("content", "")

                if kind == "accessibility_map":
                    for line in content.splitlines():
                        line = line.strip()
                        # Skip header/metadata lines
                        if (
                            line
                            and not line.startswith("ACCESSIBILITY_IDS")
                            and not line.startswith("path:")
                        ):
                            formatted = f"`{line}`"
                            if formatted not in elements:
                                elements.append(formatted)

            # Also collect IDs surfaced via RAG metadata
            for aid in result.get("accessibility_ids", []):
                formatted = f"`{aid}`"
                if formatted not in elements:
                    elements.append(formatted)

            logger.info("Extracted %d accessibility IDs", len(elements))
            return elements[:30]

        except Exception as e:
            logger.warning("Failed to extract UI elements: %s", e)
            return []
    
    def _extract_sample_code(self) -> str:
        """Get a sample code snippet to understand the app"""
        try:
            result = self.rag_service.query("View body", k=1)
            
            if result.get("code_snippets"):
                snippet = result["code_snippets"][0]
                return snippet.get("content", "")[:500]  # First 500 chars
            
            return ""
            
        except Exception as e:
            logger.warning(f"Failed to extract sample code: {e}")
            return ""
    
    def _build_context_doc(self, screens: List[str], navigation: Dict, 
                          ui_elements: List[str], sample_code: str) -> str:
        """Build the markdown document"""
        
        doc = f"""# App Context (Auto-Generated from Codebase)

**Generated:** This file was automatically created by analyzing your app's source code.  
**Last Updated:** {self._get_timestamp()}

---

## Screens

The following screens/views were detected in your codebase:

"""
        if screens:
            for screen in screens:
                doc += f"- {screen}\n"
        else:
            doc += "- (No screens detected - make sure code is indexed)\n"
        
        doc += "\n---\n\n## Navigation Patterns\n\n"
        
        if navigation["patterns"]:
            for pattern in navigation["patterns"]:
                doc += f"- {pattern}\n"
        else:
            doc += "- (No navigation patterns detected)\n"
        
        if navigation["entry_screen"]:
            doc += f"\n**Entry Screen:** {navigation['entry_screen']}\n"
        
        if navigation.get("tabs"):
            doc += f"\n**Tabs:** {', '.join(navigation['tabs'])}\n"
        
        doc += "\n---\n\n## Common UI Elements\n\n"
        doc += "Accessibility identifiers found in codebase:\n\n"
        
        if ui_elements:
            for element in ui_elements[:15]:  # Top 15
                doc += f"- {element}\n"
        else:
            doc += "- (No accessibility identifiers detected)\n"
        
        doc += "\n---\n\n## Notes\n\n"
        doc += "- This context is auto-generated from your indexed codebase\n"
        doc += "- Run `python -m app.cli generate-context` to regenerate\n"
        doc += "- Edit this file to add more specific information\n"
        doc += "- Include test credentials, expected behaviors, etc.\n"
        
        return doc
    
    def _get_template(self) -> str:
        """Fallback template if extraction fails"""
        return """# App Context

## Overview

Describe your app here (auto-extraction failed).

## Main Features

1. Feature 1
2. Feature 2

## User Flows

Describe common user flows.

---

**Note:** Auto-generation failed. Fill this out manually or check RAG indexing.
"""
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def save_to_file(self, output_path: str = "APP_CONTEXT.md") -> bool:
        """Extract context and save to file"""
        try:
            context = self.extract_context()
            
            with open(output_path, 'w') as f:
                f.write(context)
            
            logger.info(f"Saved app context to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save app context: {e}")
            return False
