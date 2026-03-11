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
    
    def _extract_screens(self) -> List[str]:
        """Extract screen/view names from RAG index"""
        try:
            # Query RAG for screens - use broader query
            result = self.rag_service.query("View struct SwiftUI", k=30)
            
            logger.info(f"Screen query returned {len(result.get('code_snippets', []))} snippets")
            
            screens = []
            for snippet in result.get("code_snippets", []):
                # Get screen name from metadata (more reliable)
                screen_name = snippet.get("screen")
                kind = snippet.get("kind")
                
                logger.debug(f"Snippet: kind={kind}, screen={screen_name}")
                
                if screen_name:
                    # Filter out non-view types
                    if screen_name not in screens and (
                        "View" in screen_name or 
                        kind == "swiftui_view"
                    ):
                        screens.append(screen_name)
                        logger.debug(f"Added screen: {screen_name}")
            
            logger.info(f"Extracted {len(screens)} screens")
            return sorted(screens)
            
        except Exception as e:
            logger.warning(f"Failed to extract screens: {e}")
            return []
    
    def _extract_navigation(self) -> Dict:
        """Extract navigation patterns"""
        try:
            result = self.rag_service.query("TabView NavigationStack ContentView", k=15)
            
            nav_info = {
                "patterns": [],
                "entry_screen": None,
                "tabs": []
            }
            
            for snippet in result.get("code_snippets", []):
                content = snippet.get("content", "")
                screen_name = snippet.get("screen", "")
                
                # Detect patterns
                if "NavigationLink" in content or "NavigationStack" in content:
                    if "NavigationStack" not in [p.split()[0] for p in nav_info["patterns"]]:
                        nav_info["patterns"].append("NavigationStack (push navigation)")
                if "TabView" in content:
                    if "TabView" not in [p.split()[0] for p in nav_info["patterns"]]:
                        nav_info["patterns"].append("TabView (tab-based navigation)")
                if "sheet" in content or ".sheet(" in content:
                    if "Modal" not in [p.split()[0] for p in nav_info["patterns"]]:
                        nav_info["patterns"].append("Modal sheets")
                
                # Extract tab labels
                if "tabItem" in content and "Label(" in content:
                    lines = content.split("\n")
                    for line in lines:
                        if 'Label("' in line and "tabItem" in content:
                            # Extract: Label("Items", ...) → "Items"
                            parts = line.split('Label("')
                            if len(parts) > 1:
                                tab_name = parts[1].split('"')[0]
                                if tab_name not in nav_info["tabs"]:
                                    nav_info["tabs"].append(tab_name)
                
                # Find entry point from ContentView or similar
                if "ContentView" in screen_name or "App" in screen_name:
                    # Look for LoginView or initial view
                    if "LoginView()" in content:
                        nav_info["entry_screen"] = "LoginView"
                    elif "MainTabView()" in content:
                        nav_info["entry_screen"] = "MainTabView"
            
            return nav_info
            
        except Exception as e:
            logger.warning(f"Failed to extract navigation: {e}")
            return {"patterns": [], "entry_screen": None, "tabs": []}
    
    def _extract_ui_elements(self) -> List[str]:
        """Extract common UI elements and accessibility IDs"""
        try:
            # Query for accessibility_map kind - this has all IDs listed!
            # Use broader query to get all accessibility maps
            result = self.rag_service.query("ACCESSIBILITY_IDS login profile item", k=25)
            
            logger.info(f"UI elements query returned {len(result.get('code_snippets', []))} snippets")
            
            elements = []
            for snippet in result.get("code_snippets", []):
                kind = snippet.get("kind", "")
                content = snippet.get("content", "")
                
                logger.debug(f"UI snippet: kind={kind}, content_preview={content[:50]}")
                
                # accessibility_map kind has IDs listed line by line
                if kind == "accessibility_map":
                    logger.info(f"Found accessibility_map, extracting IDs...")
                    lines = content.split("\n")
                    for line in lines:
                        line = line.strip()
                        # Skip header lines
                        if line and not line.startswith("ACCESSIBILITY_IDS") and not line.startswith("path:"):
                            # This is an ID!
                            if line not in elements:
                                elements.append(f"`{line}`")
                                logger.debug(f"Added ID: {line}")
            
            logger.info(f"Extracted {len(elements)} accessibility IDs")
            return elements[:30]  # Top 30 IDs
            
        except Exception as e:
            logger.warning(f"Failed to extract UI elements: {e}")
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
