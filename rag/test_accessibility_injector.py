"""Unit tests for rag.accessibility_injector"""

import textwrap
from pathlib import Path

import pytest

from rag.accessibility_injector import inject_directory, restore_files


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def write_swift(tmp_path: Path, filename: str, content: str) -> Path:
    """Write a Swift file under tmp_path and return its Path."""
    p = tmp_path / filename
    p.write_text(textwrap.dedent(content))
    return p


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestSimpleButtonInjection:
    """Simple Button without an existing .accessibilityIdentifier gets one injected."""

    def test_button_gets_accessibility_id(self, tmp_path):
        src = write_swift(
            tmp_path,
            "FeedScreen.swift",
            """\
            import SwiftUI

            struct FeedScreen: View {
                var body: some View {
                    Button("Refresh") { }
                }
            }
            """,
        )

        backup = inject_directory(tmp_path)
        modified = src.read_text()

        assert ".accessibilityIdentifier" in modified, (
            "Button should have an accessibility identifier injected"
        )
        assert "FeedScreen_button" in modified, (
            "Injected ID should follow FileName_elementType convention"
        )

        restore_files(backup)
        assert src.read_text() == textwrap.dedent("""\
            import SwiftUI

            struct FeedScreen: View {
                var body: some View {
                    Button("Refresh") { }
                }
            }
            """), "File should be restored to its original content"


class TestTextFieldInjection:
    """TextField without an identifier gets one injected."""

    def test_textfield_gets_accessibility_id(self, tmp_path):
        src = write_swift(
            tmp_path,
            "LoginScreen.swift",
            """\
            import SwiftUI

            struct LoginScreen: View {
                @State private var username = ""

                var body: some View {
                    TextField("Username", text: $username)
                }
            }
            """,
        )

        backup = inject_directory(tmp_path)
        modified = src.read_text()

        assert ".accessibilityIdentifier" in modified
        assert "LoginScreen_textField" in modified, (
            "Injected ID should include 'textField' element type"
        )

        restore_files(backup)


class TestSkipIfAlreadyHasIdentifier:
    """Elements that already have .accessibilityIdentifier must NOT be modified."""

    def test_existing_identifier_is_preserved(self, tmp_path):
        original = textwrap.dedent("""\
            import SwiftUI

            struct ProfileScreen: View {
                var body: some View {
                    Button("Save")
                        .accessibilityIdentifier("profileSaveButton")
                }
            }
            """)
        src = write_swift(tmp_path, "ProfileScreen.swift", original)

        backup = inject_directory(tmp_path)
        modified = src.read_text()

        # The explicit identifier must be untouched
        assert 'accessibilityIdentifier("profileSaveButton")' in modified, (
            "Existing explicit accessibility identifier must not be changed"
        )
        # Should not gain a second/duplicate identifier for the same element
        assert modified.count(".accessibilityIdentifier") == 1, (
            "No duplicate identifiers should be injected onto an already-tagged element"
        )

        restore_files(backup)


class TestNonViewFileUnchanged:
    """Non-View Swift files (e.g., models, services) should be left untouched."""

    def test_model_file_not_modified(self, tmp_path):
        original = textwrap.dedent("""\
            import Foundation

            struct FeedItem: Codable {
                let id: String
                let title: String
            }
            """)
        src = write_swift(tmp_path, "FeedItem.swift", original)

        backup = inject_directory(tmp_path)
        modified = src.read_text()

        assert modified == original, (
            "Model/non-View Swift files should not be modified by accessibility injection"
        )

        restore_files(backup)


class TestButtonWithTrailingClosure:
    """Button written with trailing closure syntax gets an identifier."""

    def test_trailing_closure_button_injected(self, tmp_path):
        src = write_swift(
            tmp_path,
            "ContentView.swift",
            """\
            import SwiftUI

            struct ContentView: View {
                var body: some View {
                    Button {
                        print("tapped")
                    } label: {
                        Text("Go")
                    }
                }
            }
            """,
        )

        backup = inject_directory(tmp_path)
        modified = src.read_text()

        assert ".accessibilityIdentifier" in modified, (
            "Button with trailing closure syntax should receive an accessibility identifier"
        )
        assert "ContentView_button" in modified

        restore_files(backup)


class TestRestoreFilesGuarantee:
    """restore_files must always revert ALL injected files, even when multiple exist."""

    def test_multiple_files_all_restored(self, tmp_path):
        originals: dict[str, str] = {}
        for name in ("HomeScreen.swift", "SettingsScreen.swift"):
            content = textwrap.dedent(f"""\
                import SwiftUI

                struct {name.replace('.swift', '')}: View {{
                    var body: some View {{
                        Button("Tap me") {{ }}
                    }}
                }}
                """)
            write_swift(tmp_path, name, content)
            originals[name] = content

        backup = inject_directory(tmp_path)
        restore_files(backup)

        for name, original in originals.items():
            restored = (tmp_path / name).read_text()
            assert restored == original, (
                f"{name} was not correctly restored to its original content"
            )
