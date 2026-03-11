"""
rag/auditor.py

Heuristic accessibility audit: flags screens with interactive elements but no
accessibility identifiers.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from rag.chunker import (
    Chunk,
    SWIFTUI_A11Y_ID_RE,
    SWIFTUI_INTERACTIVE_RE,
    UIKIT_A11Y_ID_RE,
    UIKIT_INTERACTIVE_RE,
)


@dataclass
class AuditFinding:
    path: str
    screen: str
    ui: str
    interactive_count: int
    accessibility_id_count: int


def audit_accessibility(
    chunks: List[Chunk],
) -> Tuple[List[AuditFinding], Dict[str, object]]:
    """
    For each SwiftUI View / UIViewController block, count interactive elements
    and accessibility IDs.  Flag screens that have interactive elements but 0 IDs.
    """
    findings: List[AuditFinding] = []

    for ch in chunks:
        kind = ch.meta.get("kind")

        if kind == "swiftui_view":
            block = ch.text
            interactive = len(SWIFTUI_INTERACTIVE_RE.findall(block))
            ids = len(SWIFTUI_A11Y_ID_RE.findall(block))
            if interactive > 0 and ids == 0:
                findings.append(AuditFinding(
                    path=str(ch.meta.get("path")),
                    screen=str(ch.meta.get("screen")),
                    ui="SwiftUI",
                    interactive_count=interactive,
                    accessibility_id_count=ids,
                ))

        if kind == "uikit_viewcontroller":
            block = ch.text
            interactive = len(UIKIT_INTERACTIVE_RE.findall(block))
            ids = len(UIKIT_A11Y_ID_RE.findall(block))
            if interactive > 0 and ids == 0:
                findings.append(AuditFinding(
                    path=str(ch.meta.get("path")),
                    screen=str(ch.meta.get("screen")),
                    ui="UIKit",
                    interactive_count=interactive,
                    accessibility_id_count=ids,
                ))

    summary: Dict[str, object] = {
        "flagged_screens": len(findings),
        "note": (
            "Heuristic audit: interactive elements exist but no accessibility "
            "identifiers were detected inside the screen block."
        ),
    }
    return findings, summary
