import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import shutil
import tempfile

# Ensure shared module is available
sys.path.append(str(Path(__file__).parent.parent))

from textual.widgets import Label, Button, Input, TextArea, Checkbox
from shared.tui import ReleaseTab

class TestReleaseTab(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.project_dir = self.test_dir / "project"
        self.project_dir.mkdir()

        # Mock release functions
        self.patcher_latest_tag = patch("shared.tui.get_latest_tag")
        self.mock_get_latest_tag = self.patcher_latest_tag.start()

        self.patcher_commits = patch("shared.tui.get_commits_since_tag")
        self.mock_get_commits = self.patcher_commits.start()

        self.patcher_next_ver = patch("shared.tui.determine_next_version")
        self.mock_determine_next = self.patcher_next_ver.start()

        self.patcher_changelog = patch("shared.tui.generate_changelog")
        self.mock_generate_changelog = self.patcher_changelog.start()

        self.patcher_perform = patch("shared.tui.perform_release")
        self.mock_perform = self.patcher_perform.start()

        self.patcher_parse = patch("shared.tui.parse_current_version")
        self.mock_parse = self.patcher_parse.start()

        # Default mocks
        self.mock_get_latest_tag.return_value = "v1.0.0"
        self.mock_get_commits.return_value = [{"hash": "abc", "subject": "feat: new", "body": ""}]
        self.mock_parse.return_value = "1.0.0"
        self.mock_determine_next.return_value = "1.1.0"
        self.mock_generate_changelog.return_value = "# v1.1.0\n- feat: new"
        self.mock_perform.return_value = (True, "Success")

    def tearDown(self):
        self.patcher_latest_tag.stop()
        self.patcher_commits.stop()
        self.patcher_next_ver.stop()
        self.patcher_changelog.stop()
        self.patcher_perform.stop()
        self.patcher_parse.stop()
        shutil.rmtree(self.test_dir)

    async def test_load_status(self):
        """Test initial status load."""
        tab = ReleaseTab(self.project_dir)
        from textual.app import App
        class TestApp(App):
            def compose(self):
                yield tab

        app = TestApp()
        async with app.run_test(size=(320, 80)) as pilot:
            # Check status label
            status_lbl = app.query_one("#release-status-lbl", Label)
            # In Textual 0.73, renderable might be accessed differently or we check the render result
            # However, for simple Labels updated with text, checking the renderable string usually works.
            # If renderable is missing, it might be _renderable (private) or we need another way.
            # Let's try checking the widget's render output.
            self.assertIn("v1.0.0", str(status_lbl.render()))

            # Check version input populated
            ver_input = app.query_one("#release-version-input", Input)
            self.assertEqual(ver_input.value, "1.1.0")

    async def test_generate_preview(self):
        """Test generating changelog preview."""
        tab = ReleaseTab(self.project_dir)
        from textual.app import App
        class TestApp(App):
            def compose(self):
                yield tab

        app = TestApp()
        async with app.run_test(size=(320, 80)) as pilot:
            # Click generate (using focus + enter to avoid OutOfBounds)
            app.set_focus(app.query_one("#btn-release-gen"))
            await pilot.press("enter")

            # Verify preview text
            preview = app.query_one("#release-changelog-editor", TextArea)
            self.assertEqual(preview.text, "# v1.1.0\n- feat: new")

            # Check release button enabled
            btn_release = app.query_one("#btn-release-exec", Button)
            self.assertFalse(btn_release.disabled)

    async def test_execute_release(self):
        """Test executing the release."""
        tab = ReleaseTab(self.project_dir)
        from textual.app import App
        class TestApp(App):
            def compose(self):
                yield tab

        app = TestApp()
        async with app.run_test(size=(320, 80)) as pilot:
            # Generate first to enable button
            app.set_focus(app.query_one("#btn-release-gen"))
            await pilot.press("enter")

            # Click release
            app.set_focus(app.query_one("#btn-release-exec"))
            await pilot.press("enter")

            # Verify calls
            self.mock_perform.assert_called_with(
                self.project_dir,
                "1.1.0",
                "# v1.1.0\n- feat: new",
                dry_run=False
            )

            # Verify success message
            lbl = app.query_one("#release-result-lbl", Label)
            self.assertIn("Success", str(lbl.render()))

    async def test_dry_run(self):
        """Test dry run option."""
        tab = ReleaseTab(self.project_dir)
        from textual.app import App
        class TestApp(App):
            def compose(self):
                yield tab

        app = TestApp()
        async with app.run_test(size=(320, 80)) as pilot:
            app.set_focus(app.query_one("#btn-release-gen"))
            await pilot.press("enter")

            # Enable dry run check
            checkbox = app.query_one("#chk-release-dry", Checkbox)
            checkbox.value = True

            app.set_focus(app.query_one("#btn-release-exec"))
            await pilot.press("enter")

            self.mock_perform.assert_called_with(
                self.project_dir,
                "1.1.0",
                "# v1.1.0\n- feat: new",
                dry_run=True
            )

if __name__ == "__main__":
    unittest.main()
