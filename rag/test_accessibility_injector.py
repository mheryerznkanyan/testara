"""Unit tests for rag.accessibility_injector"""

import textwrap
from pathlib import Path

import pytest

from rag.accessibility_injector import (
    inject_directory,
    inject_accessibility_ids,
    restore_files,
)


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


class TestButtonActionLabelExtraction:
    """Button(action:) { } with trailing label closure should extract Text label."""

    def test_button_action_extracts_label(self, tmp_path):
        src = write_swift(
            tmp_path,
            "SettingsScreen.swift",
            """\
            import SwiftUI

            struct SettingsScreen: View {
                var body: some View {
                    Button(action: {
                        doSomething()
                    }) {
                        Text("Save Changes")
                    }
                }
            }
            """,
        )

        backup = inject_directory(tmp_path)
        modified = src.read_text()

        assert "SettingsScreen_button_saveChanges" in modified, (
            "Button(action:) should extract label from trailing Text closure"
        )
        restore_files(backup)


class TestButtonClosureLabelExtraction:
    """Button { } label: { } should extract Text label from the label closure."""

    def test_button_closure_extracts_label(self, tmp_path):
        src = write_swift(
            tmp_path,
            "ProfileScreen.swift",
            """\
            import SwiftUI

            struct ProfileScreen: View {
                var body: some View {
                    Button {
                        print("tapped")
                    } label: {
                        Text("Edit Profile")
                    }
                }
            }
            """,
        )

        backup = inject_directory(tmp_path)
        modified = src.read_text()

        assert "ProfileScreen_button_editProfile" in modified, (
            "Button { } label: { } should extract label from Text in label closure"
        )
        restore_files(backup)


class TestTabItemImageFallback:
    """tabItem with only Image(systemName:) should derive semantic label from SF Symbol."""

    def test_tabitem_uses_sf_symbol_label(self, tmp_path):
        src = write_swift(
            tmp_path,
            "MainView.swift",
            """\
            import SwiftUI

            struct MainView: View {
                var body: some View {
                    TabView {
                        Text("Home")
                            .tabItem {
                                Image(systemName: "house.fill")
                            }
                        Text("Settings")
                            .tabItem {
                                Image(systemName: "gear")
                            }
                    }
                }
            }
            """,
        )

        backup = inject_directory(tmp_path)
        modified = src.read_text()

        assert "MainView_tab_home" in modified, (
            "tabItem with Image(systemName: 'house.fill') should map to 'home'"
        )
        assert "MainView_tab_settings" in modified, (
            "tabItem with Image(systemName: 'gear') should map to 'settings'"
        )
        restore_files(backup)


class TestTabItemTextPreferred:
    """tabItem with both Text and Image should prefer Text label."""

    def test_tabitem_prefers_text(self, tmp_path):
        src = write_swift(
            tmp_path,
            "AppView.swift",
            """\
            import SwiftUI

            struct AppView: View {
                var body: some View {
                    TabView {
                        Text("Content")
                            .tabItem {
                                Image(systemName: "house.fill")
                                Text("Home")
                            }
                    }
                }
            }
            """,
        )

        backup = inject_directory(tmp_path)
        modified = src.read_text()

        assert "AppView_tab_home" in modified, (
            "tabItem with both Image and Text should prefer Text label"
        )
        restore_files(backup)


class TestForEachInterpolation:
    """Elements inside ForEach should use string interpolation with the loop variable."""

    def test_foreach_button_uses_interpolation(self, tmp_path):
        src = write_swift(
            tmp_path,
            "ListScreen.swift",
            """\
            import SwiftUI

            struct ListScreen: View {
                let items = ["A", "B", "C"]

                var body: some View {
                    ForEach(items, id: \\.self) { item in
                        Button("Select") {
                            print(item)
                        }
                    }
                }
            }
            """,
        )

        backup = inject_directory(tmp_path)
        modified = src.read_text()

        assert "\\(item)" in modified, (
            "Button inside ForEach should use string interpolation with loop variable"
        )
        assert "ListScreen_button_select" in modified, (
            "Should still extract the button label"
        )
        restore_files(backup)


class TestForceReinjection:
    """force=True should strip old auto-injected IDs and re-inject with latest logic."""

    def test_force_replaces_old_ids(self, tmp_path):
        # Source with an old auto-injected numeric ID
        src = write_swift(
            tmp_path,
            "HomeScreen.swift",
            """\
            import SwiftUI

            struct HomeScreen: View {
                var body: some View {
                    Button(action: {
                        doSomething()
                    }) {
                        Text("Log Out")
                    }
                    .accessibilityIdentifier("HomeScreen_button_0")
                }
            }
            """,
        )

        backup = inject_directory(tmp_path, force=True)
        modified = src.read_text()

        # Old numeric ID should be gone
        assert "HomeScreen_button_0" not in modified, (
            "Old auto-injected numeric ID should be stripped when force=True"
        )
        # New semantic ID should be present
        assert "HomeScreen_button_logOut" in modified, (
            "Should re-inject with extracted label"
        )
        restore_files(backup)

    def test_force_preserves_manual_ids(self, tmp_path):
        src = write_swift(
            tmp_path,
            "ProfileScreen.swift",
            """\
            import SwiftUI

            struct ProfileScreen: View {
                var body: some View {
                    Button("Save")
                        .accessibilityIdentifier("myCustomSaveButton")
                }
            }
            """,
        )

        backup = inject_directory(tmp_path, force=True)
        modified = src.read_text()

        assert 'accessibilityIdentifier("myCustomSaveButton")' in modified, (
            "Manually authored IDs must never be stripped, even with force=True"
        )
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


# ---------------------------------------------------------------------------
# New element type tests
# ---------------------------------------------------------------------------


class TestNavigationLinkInjection:
    """NavigationLink elements get accessibility identifiers."""

    def test_simple_navlink(self, tmp_path):
        src = write_swift(
            tmp_path,
            "HomeScreen.swift",
            """\
            import SwiftUI

            struct HomeScreen: View {
                var body: some View {
                    NavigationLink("Settings") {
                        SettingsView()
                    }
                }
            }
            """,
        )

        backup = inject_directory(tmp_path)
        modified = src.read_text()

        assert "HomeScreen_navigationLink_settings" in modified
        restore_files(backup)

    def test_navlink_destination(self, tmp_path):
        src = write_swift(
            tmp_path,
            "MenuScreen.swift",
            """\
            import SwiftUI

            struct MenuScreen: View {
                var body: some View {
                    NavigationLink(destination: DetailView()) {
                        Text("View Details")
                    }
                }
            }
            """,
        )

        backup = inject_directory(tmp_path)
        modified = src.read_text()

        assert "MenuScreen_navigationLink_viewDetails" in modified
        restore_files(backup)


class TestPickerInjection:
    """Picker elements get accessibility identifiers."""

    def test_picker_gets_id(self, tmp_path):
        src = write_swift(
            tmp_path,
            "SettingsScreen.swift",
            """\
            import SwiftUI

            struct SettingsScreen: View {
                @State private var language = "en"

                var body: some View {
                    Picker("Language", selection: $language) {
                        Text("English").tag("en")
                        Text("Spanish").tag("es")
                    }
                }
            }
            """,
        )

        backup = inject_directory(tmp_path)
        modified = src.read_text()

        assert "SettingsScreen_picker_language" in modified
        restore_files(backup)


class TestSliderInjection:
    """Slider elements use $binding name as disambiguator."""

    def test_slider_uses_binding(self, tmp_path):
        src = write_swift(
            tmp_path,
            "PlayerView.swift",
            """\
            import SwiftUI

            struct PlayerView: View {
                @State private var volume: Double = 0.5

                var body: some View {
                    Slider(value: $volume, in: 0...1)
                }
            }
            """,
        )

        backup = inject_directory(tmp_path)
        modified = src.read_text()

        assert "PlayerView_slider_volume" in modified
        restore_files(backup)


class TestStepperInjection:
    """Stepper elements get accessibility identifiers."""

    def test_stepper_gets_id(self, tmp_path):
        src = write_swift(
            tmp_path,
            "QuantityView.swift",
            """\
            import SwiftUI

            struct QuantityView: View {
                @State private var qty = 1

                var body: some View {
                    Stepper("Quantity", value: $qty, in: 1...10)
                }
            }
            """,
        )

        backup = inject_directory(tmp_path)
        modified = src.read_text()

        assert "QuantityView_stepper_quantity" in modified
        restore_files(backup)


class TestDatePickerInjection:
    """DatePicker elements get accessibility identifiers."""

    def test_datepicker_gets_id(self, tmp_path):
        src = write_swift(
            tmp_path,
            "BookingScreen.swift",
            """\
            import SwiftUI

            struct BookingScreen: View {
                @State private var date = Date()

                var body: some View {
                    DatePicker("Check-in Date", selection: $date)
                }
            }
            """,
        )

        backup = inject_directory(tmp_path)
        modified = src.read_text()

        assert "BookingScreen_datePicker_checkInDate" in modified
        restore_files(backup)


class TestMenuInjection:
    """Menu elements get accessibility identifiers and accessibilityElement."""

    def test_menu_gets_id_and_element(self, tmp_path):
        src = write_swift(
            tmp_path,
            "ToolbarView.swift",
            """\
            import SwiftUI

            struct ToolbarView: View {
                var body: some View {
                    Menu("Options") {
                        Button("Copy") { }
                        Button("Paste") { }
                    }
                }
            }
            """,
        )

        backup = inject_directory(tmp_path)
        modified = src.read_text()

        assert "ToolbarView_menu_options" in modified
        assert ".accessibilityElement(true)" in modified, (
            "Menu should get .accessibilityElement(true) as a container element"
        )
        restore_files(backup)


class TestLinkInjection:
    """Link elements get accessibility identifiers."""

    def test_link_gets_id(self, tmp_path):
        src = write_swift(
            tmp_path,
            "AboutScreen.swift",
            """\
            import SwiftUI

            struct AboutScreen: View {
                var body: some View {
                    Link("Visit Website", destination: URL(string: "https://example.com")!)
                }
            }
            """,
        )

        backup = inject_directory(tmp_path)
        modified = src.read_text()

        assert "AboutScreen_link_visitWebsite" in modified
        restore_files(backup)


class TestTappableTextInjection:
    """Text with .onTapGesture gets accessibility identifiers."""

    def test_tappable_text_gets_id(self, tmp_path):
        src = write_swift(
            tmp_path,
            "LoginScreen.swift",
            """\
            import SwiftUI

            struct LoginScreen: View {
                var body: some View {
                    Text("Forgot Password?")
                        .onTapGesture {
                            showReset()
                        }
                }
            }
            """,
        )

        backup = inject_directory(tmp_path)
        modified = src.read_text()

        assert "LoginScreen_tappableText_forgotPassword" in modified
        restore_files(backup)

    def test_non_tappable_text_ignored(self, tmp_path):
        """Plain Text without .onTapGesture should NOT get an ID."""
        src = write_swift(
            tmp_path,
            "InfoScreen.swift",
            """\
            import SwiftUI

            struct InfoScreen: View {
                var body: some View {
                    Text("Just a label")
                }
            }
            """,
        )

        backup = inject_directory(tmp_path)
        modified = src.read_text()

        assert "tappableText" not in modified, (
            "Plain Text without onTapGesture should not get a tappableText ID"
        )
        restore_files(backup)


class TestEnclosingStructName:
    """IDs should use the enclosing struct name, not the file stem."""

    def test_struct_name_used_over_file_stem(self):
        source = textwrap.dedent("""\
            import SwiftUI

            struct MyCustomView: View {
                var body: some View {
                    Button("Tap") { }
                }
            }
        """)

        # file_stem is different from struct name
        result = inject_accessibility_ids(source, "SomeOtherFile")

        assert "MyCustomView_button_tap" in result, (
            "Should use the enclosing struct name, not the file stem"
        )
        assert "SomeOtherFile_button" not in result

    def test_multiple_views_in_file(self):
        source = textwrap.dedent("""\
            import SwiftUI

            struct FirstView: View {
                var body: some View {
                    Button("Alpha") { }
                }
            }

            struct SecondView: View {
                var body: some View {
                    Button("Beta") { }
                }
            }
        """)

        result = inject_accessibility_ids(source, "SharedFile")

        assert "FirstView_button_alpha" in result
        assert "SecondView_button_beta" in result

    def test_fallback_to_file_stem(self):
        """When struct can't be determined, fall back to file_stem."""
        source = textwrap.dedent("""\
            import SwiftUI

            struct SomeView: View {
                var body: some View {
                    Button("Go") { }
                }
            }
        """)

        result = inject_accessibility_ids(source, "SomeView")

        assert "SomeView_button_go" in result


class TestBindingDisambiguator:
    """$binding names are used as fallback disambiguator."""

    def test_textfield_binding_fallback(self):
        """When label matches but binding provides extra context."""
        source = textwrap.dedent("""\
            import SwiftUI

            struct FormView: View {
                @State private var emailAddress = ""

                var body: some View {
                    Slider(value: $brightness, in: 0...1)
                }
            }
        """)

        result = inject_accessibility_ids(source, "FormView")

        assert "FormView_slider_brightness" in result, (
            "Slider with no label should use $binding name as disambiguator"
        )


class TestImageAssetFallback:
    """Image("assetName") is used as fallback label in closures."""

    def test_button_with_named_image(self, tmp_path):
        src = write_swift(
            tmp_path,
            "NavBar.swift",
            """\
            import SwiftUI

            struct NavBar: View {
                var body: some View {
                    Button {
                        goBack()
                    } label: {
                        Image("custom_back_arrow")
                    }
                }
            }
            """,
        )

        backup = inject_directory(tmp_path)
        modified = src.read_text()

        assert "NavBar_button_customBackArrow" in modified, (
            "Button label closure with Image('assetName') should use asset name"
        )
        restore_files(backup)


class TestNavigationLinkAccessibilityElement:
    """NavigationLink should get .accessibilityElement(true)."""

    def test_navlink_gets_accessibility_element(self, tmp_path):
        src = write_swift(
            tmp_path,
            "ListScreen.swift",
            """\
            import SwiftUI

            struct ListScreen: View {
                var body: some View {
                    NavigationLink("Details") {
                        DetailView()
                    }
                }
            }
            """,
        )

        backup = inject_directory(tmp_path)
        modified = src.read_text()

        assert "ListScreen_navigationLink_details" in modified
        assert ".accessibilityElement(true)" in modified, (
            "NavigationLink should get .accessibilityElement(true)"
        )
        restore_files(backup)


# ---------------------------------------------------------------------------
# Label sanitization tests
# ---------------------------------------------------------------------------


class TestLocalizationKeySanitization:
    """Localization keys (dotted strings) should use last segment only."""

    def test_dotted_key_uses_last_segment(self):
        source = textwrap.dedent("""\
            import SwiftUI

            struct LoginScreen: View {
                var body: some View {
                    Button("auth.button.submit") { }
                }
            }
        """)

        result = inject_accessibility_ids(source, "LoginScreen")

        assert "LoginScreen_button_submit" in result, (
            "Localization key 'auth.button.submit' should resolve to 'submit'"
        )
        assert "auth.button.submit" not in result.split(".accessibilityIdentifier")[1] if ".accessibilityIdentifier" in result else True

    def test_deeply_nested_key(self):
        source = textwrap.dedent("""\
            import SwiftUI

            struct FeedbackScreen: View {
                var body: some View {
                    Button("feedback.button.submit") { }
                }
            }
        """)

        result = inject_accessibility_ids(source, "FeedbackScreen")

        assert "FeedbackScreen_button_submit" in result


class TestStringInterpolationSkipped:
    """Labels with string interpolation should be discarded."""

    def test_interpolation_falls_back_to_numeric(self):
        source = textwrap.dedent("""\
            import SwiftUI

            struct StoryRow: View {
                let author: String
                var body: some View {
                    Button("@\\(author)") { }
                }
            }
        """)

        result = inject_accessibility_ids(source, "StoryRow")

        # Should NOT contain the interpolation as label
        assert "@\\(author)" not in result.split(".accessibilityIdentifier")[1] if ".accessibilityIdentifier" in result else True
        # Should fall back to numeric index
        assert "StoryRow_button_0" in result


class TestNumericLabelSkipped:
    """Purely numeric labels like '45' should be discarded."""

    def test_numeric_label_falls_back(self):
        source = textwrap.dedent("""\
            import SwiftUI

            struct StatsView: View {
                var body: some View {
                    Button("45") { }
                }
            }
        """)

        result = inject_accessibility_ids(source, "StatsView")

        assert "StatsView_button_0" in result, (
            "Purely numeric label '45' should be discarded, falling back to index"
        )
        assert "button_45" not in result


class TestCollisionSuffixReadable:
    """Duplicate disambiguators should get _N suffix, not concatenated index."""

    def test_collision_uses_underscore_separator(self):
        source = textwrap.dedent("""\
            import SwiftUI

            struct SettingsScreen: View {
                var body: some View {
                    Toggle("Theme", isOn: $dark)
                    Toggle("Theme", isOn: $light)
                }
            }
        """)

        result = inject_accessibility_ids(source, "SettingsScreen")

        assert "SettingsScreen_toggle_theme" in result, (
            "First occurrence should be 'theme'"
        )
        assert "SettingsScreen_toggle_theme_1" in result, (
            "Second occurrence should be 'theme_1', not 'theme1'"
        )


class TestSpecialCharsStripped:
    """Special characters like ? ! @ should be stripped from IDs."""

    def test_question_mark_stripped(self):
        source = textwrap.dedent("""\
            import SwiftUI

            struct HelpScreen: View {
                var body: some View {
                    Button("Need Help?") { }
                }
            }
        """)

        result = inject_accessibility_ids(source, "HelpScreen")

        assert "HelpScreen_button_needHelp" in result
        assert "?" not in result.split(".accessibilityIdentifier(")[1].split(")")[0] if ".accessibilityIdentifier(" in result else True
