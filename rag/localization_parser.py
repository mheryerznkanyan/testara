"""
rag/localization_parser.py

Parse Apple .xcstrings (Xcode 15+) and legacy Localizable.strings files
to extract localization key→value mappings for the RAG pipeline.

This enables the LLM to know the actual displayed text for localized
UI elements (buttons, labels, tabs) rather than guessing from code.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List

from rag.chunker import Chunk


def parse_xcstrings(file_path: Path) -> Dict[str, str]:
    """Parse an .xcstrings file and return {key: english_value} mapping.

    For keys without explicit localizations, the key itself is the
    display value (Apple convention for source-language strings).
    """
    text = file_path.read_text(encoding="utf-8", errors="ignore")
    data = json.loads(text)
    source_lang = data.get("sourceLanguage", "en")

    mapping: Dict[str, str] = {}
    for key, entry in data.get("strings", {}).items():
        if not key or not key.strip():
            continue

        # Try to get the translated value for source language
        localizations = entry.get("localizations", {})
        lang_data = localizations.get(source_lang, {})
        string_unit = lang_data.get("stringUnit", {})
        value = string_unit.get("value")

        if value:
            mapping[key] = value
        elif not localizations:
            # No localizations block = key IS the display string
            # Skip format strings and single numbers
            if "%" not in key and not key.isdigit() and len(key) > 1:
                mapping[key] = key

    return mapping


def parse_localizable_strings(file_path: Path) -> Dict[str, str]:
    """Parse a legacy Localizable.strings file (key = value format)."""
    text = file_path.read_text(encoding="utf-8", errors="ignore")
    mapping: Dict[str, str] = {}

    # Match "key" = "value";
    for m in re.finditer(r'"([^"]+)"\s*=\s*"([^"]+)"\s*;', text):
        mapping[m.group(1)] = m.group(2)

    return mapping


def build_localization_chunks(
    file_path: Path, rel_path: str
) -> List[Chunk]:
    """Build RAG chunks from a localization file.

    Creates a single chunk containing all key→value mappings formatted
    as a readable table that the LLM can use to resolve localized strings.
    """
    suffix = file_path.suffix.lower()

    if suffix == ".xcstrings":
        mapping = parse_xcstrings(file_path)
    elif suffix == ".strings":
        mapping = parse_localizable_strings(file_path)
    else:
        return []

    if not mapping:
        return []

    # Build a readable localization map
    lines = [
        "LOCALIZATION_MAP",
        f"path: {rel_path}",
        f"entries: {len(mapping)}",
        "",
        "IMPORTANT: These are the ACTUAL displayed text values in the app UI.",
        "When code uses String(localized:), NSLocalizedString(), or .title",
        "properties that reference these keys, the RIGHT side shows what the",
        "user sees on screen. Use these EXACT values (case-sensitive) when",
        "querying UI elements in tests (e.g. app.buttons[\"New\"] not app.buttons[\"new\"]).",
        "",
    ]
    for key, value in sorted(mapping.items()):
        lines.append(f'"{key}" → "{value}"')

    chunk_text = "\n".join(lines)

    return [Chunk(
        text=chunk_text[:8000],  # Cap size for very large localization files
        meta={
            "kind": "localization_map",
            "path": rel_path,
            "entry_count": len(mapping),
        },
    )]
